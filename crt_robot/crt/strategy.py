"""CRT strategy wrapper for the Phase 1 engine (romeo / sham / hybrid).

``CRTStrategy.on_bar(snapshot, state)`` is the only entry point, so the
same class can later be driven by a live feed that builds the same
Snapshot. It reads prices only through the Snapshot (via MarketData) and
keeps only derived values in a cache keyed by closed-bar counts.

Flow per mode
-------------
romeo / hybrid ("C2-close" flow, CRT-R25/R30):
  at each close of a CRT timeframe bar (``htf_allowed``) -> classify it as
  C2 against C1 -> run every gate (bias, profile, dealing range, key level
  reached, timing, confirmations, SMT score) -> if all hard gates pass the
  setup is ARMED for candle 3 -> on each LTF close run the entry models in
  ``entry_set`` -> one order -> stop / targets / time exit (groups G, H) ->
  invalidation while armed or in the trade (group I).
sham ("framing" flow, CRT-R28/R32/R33/R43):
  at each close of a 4H candle opening in ``framing_candle_opens`` with the
  D1 bias -> watch 15m for a purge of its extreme after its close, inside a
  key time -> 15m OB in key time -> limit at the OB edge, stop beyond it,
  3R (2R Friday), expiry at the end of the killzone.

Every evaluated condition is logged on the Setup (``setup.checks``).
"""

from __future__ import annotations

from collections import Counter

import numpy as np
import pandas as pd

from crt_robot.backtest.orders import LONG, SHORT, ClosePosition, ModifyStop, Order, StrategyState
from crt_robot.crt import context as ctx
from crt_robot.crt import entries, keylevels
from crt_robot.crt.bars import PARENT, Bars, MarketData, ny, ts
from crt_robot.crt.config import StrategyConfig, check_implemented
from crt_robot.crt.detector import crt_bars, find_crt, mother_index
from crt_robot.crt.setup import BEAR, BULL, Setup
from crt_robot.crt.smt import PeerFeed, candle_smt, peer_bars
from crt_robot.data.instruments import Instrument, get_instrument
from crt_robot.data.mtf import Snapshot

VIEW_TFS = ("15m", "1H", "4H", "D", "D_NY", "W")


def view_timeframes(cfg: StrategyConfig, base_tf: str = "1m") -> tuple[str, ...]:
    return tuple(t for t in VIEW_TFS if t != base_tf)


class CRTStrategy:
    def __init__(self, cfg: StrategyConfig, symbol: str = "EURUSD", peers: list[PeerFeed] | None = None,
                 instrument: Instrument | None = None, trade_from: pd.Timestamp | None = None):
        check_implemented(cfg)
        self.cfg = cfg
        self.mode = cfg.mode
        self.name = f"crt_{cfg.mode}"
        self.symbol = symbol
        self.inst = instrument or get_instrument(symbol)
        self.peers = list(peers or [])
        self.setups: list[Setup] = []          # every setup ever created (the log)
        self._live: list[Setup] = []           # candidate/armed/entered
        self._cache: dict = {}
        self._peer_cache: dict = {}
        self._last_n: dict = {}
        self._week_trades: Counter = Counter()
        self._current: Setup | None = None     # setup whose order is pending / position open
        self._be_done = False
        self._warned = False
        self._entries_seen = 0
        self.flow = "framing" if cfg.mode == "sham" else "c2_close"
        self.htfs = list(cfg.timeframes.htf_allowed)
        self.tick = self.inst.tick
        self.buffer = cfg.stop.stop_buffer_ticks * self.tick
        # warm-up: history before ``trade_from`` only feeds levels / ATR, no setups
        self.trade_from_ns = int(pd.Timestamp(trade_from).value) if trade_from is not None else None

    # ------------------------------------------------------------------
    def on_bar(self, snap: Snapshot, state: StrategyState) -> list:
        cfg = self.cfg
        md = MarketData(snap, self._cache, cfg.daily_tf, cfg.clock.weekly_candle)
        actions: list = []
        self._sync_position(md, state)
        if self._current is not None and self._current.state == "entered":
            actions += self._manage_trade(md, state)
        for htf in self.htfs:
            n = md.n_closed(htf)
            if n != self._last_n.get(htf):
                first = htf not in self._last_n
                self._last_n[htf] = n
                if not first:
                    self._on_htf_close(md, htf)
        for s in list(self._live):
            if s.state in ("armed",):
                act = self._step_armed(md, s, state)
                if act:
                    actions += act
        self._live = [s for s in self._live if s.state in ("armed", "entered")]
        return actions

    # ------------------------------------------------------------------
    # position bookkeeping
    # ------------------------------------------------------------------
    def _sync_position(self, md: MarketData, state: StrategyState) -> None:
        cur = self._current
        if cur is None:
            return
        pos = state.position
        if cur.state == "armed" and cur.order_kind:
            filled = state.entries_total > self._entries_seen
            if pos is not None and pos.tag == cur.id:
                cur.state = "entered"
                cur.entry_ns = int(pd.Timestamp(pos.entry_time).value)
                cur.entry_price = float(pos.entry)
                self._week_trades[_week_key(md.now_ns)] += 1
                self._be_done = self._warned = False
            elif filled and pos is None:
                # filled and closed on its entry bar
                cur.state = "done"
                self._week_trades[_week_key(md.now_ns)] += 1
                self._current = None
            elif not state.pending and pos is None:
                # pending order expired / was refused without a fill
                cur.state = "expired"
                cur.invalid_reason = cur.invalid_reason or "limit_not_filled"
                self._current = None
            self._entries_seen = state.entries_total
        elif cur.state == "entered" and (pos is None or pos.tag != cur.id):
            cur.state = "done"
            self._current = None

    # ------------------------------------------------------------------
    # detection
    # ------------------------------------------------------------------
    def _on_htf_close(self, md: MarketData, htf: str) -> None:
        if self.trade_from_ns is not None and md.now_ns < self.trade_from_ns:
            return
        if self.flow == "framing":
            if htf == self.cfg.timeframes.sham_stack["framing"]:
                self._detect_framing(md, htf)
        else:
            self._detect_c2(md, htf)

    def _new_setup(self, md: MarketData, htf: str, b: Bars, c1: int, direction: str, purpose: str = "trade") -> Setup:
        tfp = self.cfg.timeframes
        bar1 = b.bar(c1)
        sid = f"{self.symbol}-{self.mode}-{htf}-{ny(bar1['open_time']):%Y%m%d%H%M}-{direction}-{len(self.setups)}"
        return Setup(id=sid, symbol=self.symbol, mode=self.mode, htf=htf, ltf=tfp.tf_pairs[htf],
                     kl_tf=tfp.kl_tf_for_htf.get(htf, ""), parent_htf=PARENT.get(htf, ""), purpose=purpose,
                     direction=direction, detected_ns=md.now_ns, c1_open_ns=bar1["open_time"],
                     c1_close_ns=bar1["close_time"], c1=bar1, crt_high=bar1["high"], crt_low=bar1["low"])

    def _detect_c2(self, md: MarketData, htf: str) -> None:
        cfg = self.cfg
        b = crt_bars(md.bars(htf), cfg.clock.skip_sunday_stub)
        if len(b) < 3 or int(b.close_time[-1]) > md.now_ns:
            return
        if htf in ("D",) and md.resolve("D") == "D_NY" and ctx.is_sunday_stub(int(md.bars("D").open_time[-1])):
            return
        shape = find_crt(b, cfg.candles.max_inside_bars, cfg.general.sweep_min_ticks * self.tick * 0.999)
        if shape is None or shape.direction is None:
            return
        s = self._new_setup(md, htf, b, shape.c1, shape.direction)
        c2 = b.bar(shape.c2)
        s.c2, s.c2_open_ns, s.c2_close_ns, s.c2_class = c2, c2["open_time"], c2["close_time"], shape.outcome
        s.inside_bars = shape.inside_bars
        s.sweep_extreme = c2["low"] if s.direction == BULL else c2["high"]
        self.setups.append(s)
        s.log("CRT-R01", "htf_named", "info", f"{htf} CRT, LTF {s.ltf}, KL {s.kl_tf}, parent {s.parent_htf}")
        s.log("CRT-R24", "crt_levels", "info", f"H={s.crt_high:.5f} L={s.crt_low:.5f} 50%={s.crt_50:.5f}")
        s.log("CRT-R26", "inside_bars", "info", shape.inside_bars)
        s.log("DEF-05", "c2_class", "info", shape.outcome + (" (outside bar)" if shape.outside else ""))
        # CRT-R25 / R29 close back inside: required or scored
        req = cfg.crt.require_close_inside.get(htf, True)
        if req:
            if not s.gate("CRT-R29", "c2_close_inside", shape.close_inside, shape.outcome,
                          "required on this TF; a close beyond is a breakout (let it go)"):
                return s.reject("breakout_c2")
        else:
            s.log("C-04", "c2_close_inside", "score", 1 if (shape.close_inside and cfg.crt.close_inside_score) else 0,
                  "not required on this TF; scored")
        ltf = md.bars(s.ltf)
        sweep = self._first_sweep(ltf, s, c2["open_time"], c2["close_time"])
        s.sweep_ns = sweep
        self._common_gates(md, s, purge_extreme=s.sweep_extreme, c2_known=True)
        if s.state == "candidate":
            s.state = "armed"
            s.expiry_ns = None
            self._live.append(s)

    def _detect_framing(self, md: MarketData, htf: str) -> None:
        cfg = self.cfg
        b = md.bars(htf)
        if len(b) < 3:
            return
        k = len(b) - 1
        if ny(int(b.open_time[k])).strftime("%H:%M") not in cfg.crt.framing_candle_opens:
            return
        # DEF-27: if the framing candle sits inside an earlier candle, use the outer one
        c1, inside = mother_index(b, k + 1, cfg.candles.max_inside_bars)
        bias, structure, cls = ctx.sham_bias(crt_bars(md.bars("D"), cfg.clock.skip_sunday_stub), cfg.general.swing_n)
        direction = bias if bias in (BULL, BEAR) else BULL
        c1_open = int(b.open_time[c1])
        if any(o.c1_open_ns == c1_open and o.htf == htf and o.direction == direction for o in self.setups[-12:]):
            return          # the same mother candle is already framed (DEF-27)
        s = self._new_setup(md, htf, b, c1, direction, purpose="framing")
        s.inside_bars = inside
        self.setups.append(s)
        s.log("CRT-R01", "htf_named", "info", f"{htf} framing CRT, entry {s.ltf}, bias D")
        s.log("CRT-R28", "framing_open", "pass", ny(int(b.open_time[k])).strftime("%H:%M"))
        if not s.gate("CRT-R08", "daily_bias", bias in (BULL, BEAR), f"{bias} (structure={structure}, close={cls})",
                      "neutral daily bias -> no trade (CRT-R13)"):
            return s.reject("neutral_bias")
        s.extra["bias"] = bias
        s.state = "armed"
        s.c3_open_ns = int(b.close_time[k])
        self._live.append(s)

    def _first_sweep(self, ltf: Bars, s: Setup, a_ns: int, b_ns: int) -> int | None:
        w = ltf.between(a_ns, b_ns)
        hit = w.low < s.crt_low if s.direction == BULL else w.high > s.crt_high
        if not hit.any():
            return None
        return int(w.open_time[int(np.argmax(hit))])

    # ------------------------------------------------------------------
    # gates shared by every flow (evaluated when the purge is known)
    # ------------------------------------------------------------------
    def _common_gates(self, md: MarketData, s: Setup, purge_extreme: float, c2_known: bool) -> None:
        cfg = self.cfg
        d = s.direction
        htf_b = md.bars(s.htf)
        atr_htf = keylevels.atr_last(htf_b, cfg.general.atr_len)
        ltf_b = md.bars(s.ltf)
        atr_ltf = keylevels.atr_last(ltf_b, cfg.general.atr_len)
        before = s.c2_open_ns if s.c2_open_ns is not None else s.c1_close_ns

        # ---- B: HTF bias
        bias_tf = "W" if cfg.bias.bias_tf == "weekly" else PARENT.get(s.htf, "W")
        pb = crt_bars(md.bars(bias_tf), cfg.clock.skip_sunday_stub)
        if s.mode != "sham":
            if len(pb) >= 2:
                bias = ctx.close_wick_bias(pb.bar(len(pb) - 1), pb.bar(len(pb) - 2))
            else:
                bias = "unknown"
            s.extra["bias"] = bias
            ok = bias == d
            if cfg.bias.bias_gate == "hard":
                if not s.gate("CRT-R31", "htf_bias", ok, f"{bias_tf}:{bias}", "close/wick rule (CRT-R06) on the parent TF"):
                    return s.reject("counter_bias")
            else:
                s.log("CRT-R31", "htf_bias", "score", 1 if ok else 0, f"{bias_tf}:{bias}")
        # ---- R05 / R11: no trades against an active higher-TF CRT
        if not cfg.bias.allow_counter_htf:
            opp = [o for o in self._live if o is not s and o.direction != d and o.state in ("armed", "entered")
                   and _tf_rank(o.htf) > _tf_rank(s.htf)]
            if not s.gate("CRT-R05", "not_counter_htf", not opp, ",".join(o.id for o in opp) or "none"):
                return s.reject("counter_htf")
        # ---- G-04 market profile
        mode = cfg.bias.market_profile_mode
        if mode != "none" and len(pb) >= 3:
            if mode == "five_phase":
                phase = ctx.five_phase(pb, cfg.general.swing_n)
                outcome = ctx.OUTCOME_WITH_KL.get(phase, "range")
                ok = outcome in cfg.bias.trade_outcomes
                detail = f"{bias_tf} phase={phase} -> outcome with KL={outcome}"
            elif mode == "sham4":
                phase = ctx.sham4(pb, d)
                ok = phase == "expansion"
                detail = f"{bias_tf} sham4={phase}"
            else:
                phase = ctx.romeo_swings_profile(pb, cfg.general.swing_n, cfg.bias.profile_k)
                ok = phase in (d, "none")
                detail = f"{bias_tf} romeo profile={phase}"
            s.log("G-04", "market_profile_phase", "info", phase)
            if not s.gate("G-04", "market_profile", ok, phase, detail):
                return s.reject("market_profile")
        # ---- dealing range / premium-discount (CRT-R21, R16)
        dr_tf = s.htf if cfg.dealing_range.dr_tf == "htf" else bias_tf
        drb = md.bars(dr_tf)
        dr = md.memo(("dr", md.resolve(dr_tf), len(drb)), lambda: ctx.dealing_range(drb.tail(300), cfg))
        if dr is not None:
            eq, lo_, hi_ = dr.eq, dr.low, dr.high
            src = f"{dr_tf} DR {dr.low:.5f}-{dr.high:.5f}"
        elif len(pb) >= 1:   # PROPOSED Romeo fallback: parent candle 50%
            p = pb.bar(len(pb) - 1)
            eq, lo_, hi_ = (p["high"] + p["low"]) / 2, p["low"], p["high"]
            src = f"{bias_tf} parent candle 50%"
        else:
            eq = lo_ = hi_ = None
            src = "none"
        s.extra.update(dr_eq=eq, dr_low=lo_, dr_high=hi_)
        if eq is not None and cfg.dealing_range.require_correct_half:
            ok = s.crt_low <= eq if d == BULL else s.crt_high >= eq
            if not s.gate("CRT-R21", "correct_half", ok, f"eq={eq:.5f}", src):
                return s.reject("wrong_half")
        if cfg.dealing_range.rebalance_required and dr is not None:
            k_drb = drb.tail(300)
            reb = ctx.rebalanced(dr, k_drb, d)
            if not s.gate("CRT-R16", "dr_rebalanced", reb, src):
                return s.reject("not_rebalanced")
        # ---- C: key level reached by the purge (CRT-R18/R19/R20/R22)
        cands = keylevels.candidates(md, cfg, s.htf, d, before, s.htf)
        klb = md.bars(s.kl_tf) if s.kl_tf else None
        vis = klb.tail(cfg.key_level.visible_lookback) if klb is not None and len(klb) else None
        chosen, scored = keylevels.score_and_select(
            cands, direction=d, swept_extreme=s.swept_extreme, purge_extreme=purge_extreme, atr_htf=atr_htf,
            atr_ltf=atr_ltf, eq=eq, kl_bars_low=float(vis.low.min()) if vis is not None and len(vis) else None,
            kl_bars_high=float(vis.high.max()) if vis is not None and len(vis) else None, cfg=cfg)
        s.kl_candidates = len(cands)
        s.key_level = chosen
        detail = (f"{chosen.kind}@{chosen.tf} {chosen.bottom:.5f}-{chosen.top:.5f} score={chosen.score}"
                  if chosen else f"{len(cands)} candidates, none reached within {cfg.key_level.kl_max_dist_atr} ATR")
        if not s.gate("CRT-R18", "key_level_reached", chosen is not None, len(scored), detail):
            return s.reject("key_level_missed")
        s.log("G-01", "kl_is_bos_origin", "info", chosen.is_bos_origin)
        if chosen.is_bos_origin:
            s.log("G-01", "kl_bos_bonus", "score", cfg.key_level.kl_score_bos_bonus)
        # ---- E: timing of the purge
        conf = {}
        if s.sweep_ns is not None:
            sw = s.sweep_ns
            s.log("E", "sweep_weekday", "info", ctx.weekday(sw))
            s.log("E", "sweep_hour_ny", "info", ny(sw).hour)
            h4 = md.bars("4H")
            k4 = int(np.searchsorted(h4.open_time, sw, side="right")) - 1
            h4_open = int(h4.open_time[k4]) if k4 >= 0 and int(h4.close_time[k4]) > sw else _h4_open(sw)
            minute_in = (sw - h4_open) // 60_000_000_000
            s.log("G-05", "purge_minute_in_h4", "info", int(minute_in))
            s.log("G-22", "rhythm_159", "info", ctx.rhythm_159(h4_open))
            in_ph = ctx.in_purge_hour(sw, cfg)
            s.log("G-11", "purge_in_purge_hour", "score", 1 if in_ph else 0)
            s.log("G-11", "purge_in_refined_key_time", "info", ctx.in_refined_key_time(sw, cfg))
            timed = ctx.in_key_time(sw, cfg, purge=True)
            conf["timed_purge"] = timed
            if cfg.timing.require_timed_purge or (s.mode == "romeo" and cfg.timing.romeo_use_killzones):
                if not s.gate("CRT-R32", "timed_purge", timed, ny(sw).strftime("%a %H:%M"), "killzone/macro/purge hour"):
                    return s.reject("outside_key_time")
            if cfg.timing.closing_hour_filter != "none":
                first = minute_in < 60
                last = minute_in >= 180
                ok = first if cfg.timing.closing_hour_filter == "first" else last
                if not s.gate("G-05", "closing_hour", ok, int(minute_in)):
                    return s.reject("closing_hour")
            # G-23 turtle soup at the open of the new candle (or late in it)
            if s.c2_open_ns is not None and s.c2_close_ns is not None:
                f = ctx.frac_in_candle(sw, s.c2_open_ns, s.c2_close_ns)
                if cfg.crt.ts_timing_mode == "open_of_new":
                    s.log("G-23", "ts_at_open", "score", 1 if f <= cfg.crt.ts_at_open_frac else 0, round(f, 3))
                else:
                    s.log("G-23", "late_manip", "score", 1 if f >= cfg.crt.late_frac else 0, round(f, 3))
            # CRT-R35 / R14 weekday filter (Romeo-structure modes)
            if s.mode in ("romeo", "hybrid") and cfg.bias.use_weekly_time_theory and "all" not in cfg.bias.romeo_sweep_days:
                wd = ctx.weekday(sw)
                if not s.gate("CRT-R35", "sweep_weekday_ok", wd in cfg.bias.romeo_sweep_days, wd):
                    return s.reject("weekday")
            # G-26 skip the week if Monday was an expansion
            if s.mode in ("romeo", "hybrid") and cfg.bias.skip_if_monday_expansion:
                me = ctx.monday_expansion(md.bars("D_NY"), sw, cfg)
                if me is not None and not s.gate("G-26", "no_monday_expansion", not me, me):
                    return s.reject("monday_expansion")
        else:
            conf["timed_purge"] = False
        # ---- G-20 confirmations
        conf["timed_crt"] = (ny(s.c1_open_ns).strftime("%H:%M") in cfg.crt.timed_crt_h4_opens) if s.htf == "4H" else True
        conf["htf_key_level"] = chosen is not None
        conf["inside_bars"] = s.inside_bars > 0
        if s.c2_open_ns is not None and s.c2_close_ns is not None:
            conf["ltf_crt_inside_htf"] = entries.ltf_crt_inside(ltf_b, d, s.swept_extreme, s.c2_open_ns, s.c2_close_ns)
        else:
            end = md.now_ns
            conf["ltf_crt_inside_htf"] = entries.ltf_crt_inside(ltf_b, d, s.swept_extreme, s.c1_close_ns, end)
        n_conf = sum(bool(conf.get(t)) for t in cfg.crt.confirmation_types)
        s.log("G-20", "confirmations_count", "info", n_conf, ",".join(t for t in cfg.crt.confirmation_types if conf.get(t)))
        if not s.gate("G-20", "min_confirmations", n_conf >= cfg.crt.min_confirmations, n_conf,
                      f"need {cfg.crt.min_confirmations} of {cfg.crt.confirmation_types}"):
            return s.reject("too_few_confirmations")
        # ---- SMT (score; optional gate)
        smt_hit = self._smt(md, s)
        if smt_hit is None:
            s.log("C-24", "smt", "info", "no peer data")
        else:
            s.log("CRT-R46", "smt", "score", 1 if smt_hit else 0)
        if cfg.entry.require_smt and not s.gate("C-24", "smt_required", bool(smt_hit), smt_hit):
            return s.reject("no_smt")

    def _kl_probe(self, md: MarketData, s: Setup) -> bool:
        """Cheap check: has the purge reached any key level yet?"""
        cfg = self.cfg
        before = s.c2_open_ns if self.flow == "c2_close" else s.c1_close_ns
        cands = keylevels.candidates(md, cfg, s.htf, s.direction, before, s.htf)
        atr_htf = keylevels.atr_last(md.bars(s.htf), cfg.general.atr_len)
        atr_ltf = keylevels.atr_last(md.bars(s.ltf), cfg.general.atr_len)
        best, _ = keylevels.score_and_select(cands, direction=s.direction, swept_extreme=s.swept_extreme,
                                             purge_extreme=s.sweep_extreme, atr_htf=atr_htf, atr_ltf=atr_ltf,
                                             eq=None, kl_bars_low=None, kl_bars_high=None, cfg=cfg)
        return best is not None

    def _smt(self, md: MarketData, s: Setup) -> bool | None:
        if not self.peers or s.c2 is None:
            return None
        res = []
        for p in self.peers:
            cache = self._peer_cache.setdefault(p.name, {})
            pb = peer_bars(p, md.now_ns, md.resolve(s.htf), cache, self.cfg.daily_tf)
            c2 = s.c2
            if self.flow == "framing" and pb is not None:
                # the purge happened on the LTF: compare the peer's LTF path since C1 closed
                pl = peer_bars(p, md.now_ns, s.ltf, cache, self.cfg.daily_tf)
                seg = pl.since(s.c1_close_ns) if pl is not None else None
                if seg is None or len(seg) == 0:
                    continue
                pk = int(np.searchsorted(pb.open_time, s.c1_open_ns, side="left"))
                if pk >= len(pb) or pb.open_time[pk] != s.c1_open_ns:
                    continue
                c2 = {"open_time": s.c1_close_ns, "high": float(seg.high.max()), "low": float(seg.low.min()),
                      "close": float(seg.close[-1])}
                pb = Bars(pb.tf, np.array([s.c1_open_ns, s.c1_close_ns]), np.array([s.c1_close_ns, md.now_ns]),
                          np.array([pb.open[pk], seg.open[0]]), np.array([pb.high[pk], c2["high"]]),
                          np.array([pb.low[pk], c2["low"]]), np.array([pb.close[pk], c2["close"]]))
                ours_c2 = {"open_time": s.c1_close_ns, "high": s.sweep_extreme if s.direction == BEAR else s.c2["high"],
                           "low": s.sweep_extreme if s.direction == BULL else s.c2["low"], "close": md.last_price()}
                r = candle_smt(s.direction, s.c1, ours_c2, pb, p.inverse, self.cfg.entry.smt_take)
            else:
                r = candle_smt(s.direction, s.c1, c2, pb, p.inverse, self.cfg.entry.smt_take)
            if r is not None:
                res.append(r)
        if not res:
            return None
        return any(res)

    # ------------------------------------------------------------------
    # armed setups: entries, expiry, invalidation
    # ------------------------------------------------------------------
    def _step_armed(self, md: MarketData, s: Setup, state: StrategyState) -> list:
        cfg = self.cfg
        ltf = md.bars(s.ltf)
        n = len(ltf)
        key = ("ltf_n", s.id)
        if self._cache.get(key) == n and (self.flow == "framing" or s.c3_open_ns is not None):
            return []
        self._cache[key] = n
        now = md.now_ns
        if self._current is s:
            return []          # order already working
        if self.flow == "framing":
            return self._step_framing(md, s, ltf, state)
        # C3 timing (known from the forming HTF bar)
        if s.c3_open_ns is None:
            f = md.forming(s.htf)
            if f is None or int(f.open_time.value) < s.c2_close_ns:
                return []
            if cfg.clock.skip_sunday_stub and md.resolve(s.htf) == "D_NY" and ctx.is_sunday_stub(int(f.open_time.value)):
                return []
            s.c3_open_ns, s.c3_close_ns, s.c3_open = int(f.open_time.value), int(f.close_time.value), float(f.open)
            s.expiry_ns = s.c3_close_ns
            s.log("CRT-R30", "c3_open", "info", f"{ny(s.c3_open_ns):%a %H:%M} @ {s.c3_open:.5f}")
        if now >= (s.expiry_ns or 0):
            s.state = "expired"
            s.invalid_reason = s.invalid_reason or "no_entry_model"
            s.log("CRT-R37", "entry_model_before_expiry", "fail", None, "C3 closed without an entry")
            return []
        path = ltf.since(s.c2_close_ns)
        if self._invalidated_before_entry(s, path):
            return []
        sig, why = self._romeo_entries(md, s, ltf)
        if sig is None:
            return []
        return self._place(md, s, sig, state)

    def _invalidated_before_entry(self, s: Setup, path: Bars) -> bool:
        cfg = self.cfg
        if len(path) == 0:
            return False
        if cfg.invalidation.skip_if_50_reached:
            reached = path.high.max() >= s.crt_50 if s.direction == BULL else path.low.min() <= s.crt_50
            if reached:
                s.log("CRT-R45", "no_chasing_50_reached", "fail", None, "the 50% traded before any entry")
                s.state, s.invalid_reason = "invalidated", "chased_50_reached"
                return True
        ext = s.sweep_extreme if s.sweep_extreme is not None else s.swept_extreme
        rng = np.maximum(path.high - path.low, 1e-12)
        body = np.abs(path.close - path.open) / rng
        beyond = (path.close < ext) if s.direction == BULL else (path.close > ext)
        decisive = int((beyond & (body >= 0.5)).sum())
        if decisive >= cfg.invalidation.decisive_closes:
            s.log("CRT-R58", "decisive_closes_beyond", "fail", decisive)
            s.state, s.invalid_reason = "invalidated", "decisive_close_beyond"
            return True
        return False

    def _romeo_entries(self, md: MarketData, s: Setup, ltf: Bars):
        cfg = self.cfg
        hist = ltf.tail(len(ltf.since(s.c2_open_ns)) + 200)
        tol = cfg.key_level.kl_touch_tol * keylevels.atr_last(ltf, cfg.general.atr_len)
        tol = tol if np.isfinite(tol) else 0.0
        last_why = ""
        for kind in cfg.entry.entry_set:
            if kind == "model1":
                r = entries.model1(hist, s.direction, s.swept_extreme, s.c2_open_ns, s.c2_close_ns, md.now_ns,
                                   cfg, self.buffer)
            elif kind in ("mss", "ote"):
                if kind == "ote" and "mss" in cfg.entry.entry_set:
                    continue
                r = entries.mss_ote(hist, s.direction, s.swept_extreme, s.c2_open_ns, cfg, self.buffer, kind, tol)
            elif kind == "ob":
                r = entries.sham_ob(hist, s.direction, s.swept_extreme, s.c2_open_ns, cfg, self.buffer,
                                    lambda t: ctx.in_key_time(t, cfg), s.extra.get("dr_eq"))
            else:
                continue
            s.extra[f"entry_{kind}"] = r.detail
            if r.signal is not None:
                if r.signal.trigger_ns < s.c2_close_ns and not cfg.crt.allow_c2_entry and r.signal.order == "market":
                    continue
                return r.signal, r.detail
            last_why = r.detail
        return None, last_why

    def _step_framing(self, md: MarketData, s: Setup, ltf: Bars, state: StrategyState) -> list:
        cfg = self.cfg
        now = md.now_ns
        after = ltf.since(s.c1_close_ns)
        if not s.extra.get("gated"):
            if s.sweep_ns is None:      # waiting for the purge (CRT-R27: only after C1 closed)
                if len(after) == 0:
                    return []
                hit = after.low < s.crt_low if s.direction == BULL else after.high > s.crt_high
                if not hit.any():
                    if now - s.c1_close_ns > 24 * 3600 * 10**9:
                        s.state, s.invalid_reason = "expired", "no_purge"
                    return []
                j = int(np.argmax(hit))
                s.sweep_ns = int(after.open_time[j])
                s.c2 = {"open_time": s.sweep_ns, "close_time": int(after.close_time[j]),
                        "high": float(after.high[j]), "low": float(after.low[j]),
                        "open": float(after.open[j]), "close": float(after.close[j])}
                s.expiry_ns = _next_killzone_end(s.sweep_ns, cfg)
                s.log("CRT-R27", "purge_after_crt_close", "pass", ny(s.sweep_ns).strftime("%a %H:%M"))
                s.log("CRT-R37", "setup_expiry", "info", f"{ny(s.expiry_ns):%a %H:%M}")
            seg = after.since(s.sweep_ns)
            s.sweep_extreme = float(seg.low.min()) if s.direction == BULL else float(seg.high.max())
            # CRT-R23: the purge may tag the key level later inside the killzone; wait until expiry
            if not self._kl_probe(md, s):
                if s.check("key_level_pending") is None:
                    s.log("CRT-R23", "key_level_pending", "pending", None, "purge has not reached a key level yet")
                if now >= s.expiry_ns:
                    s.log("CRT-R23", "key_level_reached", "fail", None, "no key level tagged before the killzone ended")
                    s.state, s.invalid_reason = "invalidated", "key_level_missed"
                return []
            s.extra["gated"] = True
            self._common_gates(md, s, purge_extreme=s.sweep_extreme, c2_known=False)
            if s.state not in ("candidate", "armed"):
                return []
            s.state = "armed"
        if now >= (s.expiry_ns or 0):
            s.state, s.invalid_reason = "expired", s.invalid_reason or "no_entry_model"
            s.log("CRT-R60", "ob_before_expiry", "fail", None, "no 15m OB in the killzone")
            return []
        # R60: price keeps going against the idea
        a15 = keylevels.atr_last(ltf, cfg.general.atr_len)
        path = ltf.since(s.sweep_ns)
        if len(path) and np.isfinite(a15):
            if s.direction == BULL:
                bad = (path.close < s.crt_low - cfg.invalidation.sham_invalid_atr * a15).any()
            else:
                bad = (path.close > s.crt_high + cfg.invalidation.sham_invalid_atr * a15).any()
            if bad:
                s.log("CRT-R60", "no_close_far_beyond", "fail", None, "closed beyond the purged extreme by > ATR")
                s.state, s.invalid_reason = "invalidated", "decisive_close_beyond"
                return []
        hist = ltf.tail(len(after) + 50)
        r = entries.sham_ob(hist, s.direction, s.swept_extreme, s.c1_close_ns, cfg, self.buffer,
                            lambda t: ctx.in_key_time(t, cfg), s.extra.get("dr_eq"))
        s.extra["entry_ob"] = r.detail
        if r.status == "fail":
            s.log("CRT-R33", "ob_valid", "fail", None, r.detail)
            s.state, s.invalid_reason = "invalidated", "outside_key_time" if "key time" in r.detail else "ob_invalid"
            return []
        if r.signal is None:
            return []
        return self._place(md, s, r.signal, state)

    # ------------------------------------------------------------------
    # order construction (groups F-H, J)
    # ------------------------------------------------------------------
    def _place(self, md: MarketData, s: Setup, sig: entries.Signal, state: StrategyState) -> list:
        cfg = self.cfg
        now = md.now_ns
        d = s.direction
        side = LONG if d == BULL else SHORT
        price_ref = sig.price
        s.log("F", "entry_signal", "info", f"{sig.kind} {sig.order} @ {price_ref:.5f} stop {sig.stop:.5f}")
        # CRT-R44: bull entries below C3's open, bear above
        if self.flow == "c2_close" and s.c3_open is not None:
            ok = price_ref < s.c3_open if d == BULL else price_ref > s.c3_open
            if not s.gate("CRT-R44", "entry_vs_c3_open", ok, f"{price_ref:.5f} vs {s.c3_open:.5f}"):
                s.state, s.invalid_reason = "invalidated", "entry_beyond_c3_open"
                return []
        # G-26 never in the middle of the range
        lo_, hi_ = s.extra.get("dr_low"), s.extra.get("dr_high")
        if lo_ is not None and hi_ is not None and hi_ > lo_:
            pos = (price_ref - lo_) / (hi_ - lo_)
            a, b = cfg.bias.mid_range_block
            if not s.gate("G-26", "not_mid_range", not (a <= pos <= b), round(pos, 3)):
                s.state, s.invalid_reason = "invalidated", "mid_range"
                return []
        # Sham: no new trades in the Asia block (CRT-R34)
        if cfg.timing.use_asia_block or (s.mode == "romeo" and cfg.timing.asia_block_romeo):
            if ctx.in_asia_block(now, cfg):
                s.log("CRT-R34", "asia_block", "info", ny(now).strftime("%H:%M"), "waiting for London")
                return []
        # CRT-R66 news blackout
        ev = ctx.news_blocked(now, cfg)
        if not s.gate("CRT-R66", "no_news_blackout", not ev, ev or "none"):
            s.state, s.invalid_reason = "invalidated", "news_blackout"
            return []
        # account-level limits
        if not state.can_trade:
            s.log("CRT-R63", "account_can_trade", "fail", None, "daily stop / max trades per day")
            s.state, s.invalid_reason = "invalidated", "risk_blocked"
            return []
        if self._week_trades[_week_key(now)] >= cfg.risk.max_trades_per_week:
            s.log("CRT-R64", "max_trades_per_week", "fail", cfg.risk.max_trades_per_week)
            s.state, s.invalid_reason = "invalidated", "max_trades_per_week"
            return []
        if self._current is not None or state.position is not None or state.pending:
            s.log("J", "one_position_at_a_time", "fail", None, "another setup holds the position/order")
            s.state, s.invalid_reason = "invalidated", "busy"
            return []
        # stops (group G)
        stop = sig.stop
        if cfg.stop.stop_mode == "fvg_fill_low":
            alt = self._fvg_fill_stop(md, d)
            if alt is not None and (alt < price_ref if d == BULL else alt > price_ref):
                stop = alt - self.buffer if d == BULL else alt + self.buffer
        risk = abs(price_ref - stop)
        if risk <= 0 or (stop >= price_ref if d == BULL else stop <= price_ref):
            s.log("G", "stop_valid", "fail", stop)
            s.state, s.invalid_reason = "invalidated", "bad_stop"
            return []
        # targets (group H)
        tp1 = None
        tm = cfg.targets.target_mode
        if tm == "crt_levels":
            target = s.opposite_extreme
            beyond_50 = price_ref >= s.crt_50 if d == BULL else price_ref <= s.crt_50
            if not beyond_50 and cfg.targets.tp1_fraction > 0:
                tp1 = s.crt_50
        elif tm == "to_50_only":
            target = s.crt_50
        else:   # r_multiple
            target = price_ref + side * cfg.targets.r_target * risk
        friday = ny(now).day_of_week == 4
        if friday:
            cap = price_ref + side * cfg.targets.friday_r_target * risk
            if (target - cap) * side > 0:
                target = cap
                s.log("CRT-R67", "friday_2r_cap", "info", round(cap, 6))
            if tp1 is not None and (tp1 - target) * side >= 0:
                tp1 = None
        if (target - price_ref) * side <= 0:
            s.log("H", "target_valid", "fail", target, "target not on the profit side")
            s.state, s.invalid_reason = "invalidated", "target_behind_entry"
            return []
        s.log("H", "targets", "info", f"tp1={tp1} target={target:.5f} ({(target - price_ref) * side / risk:.2f}R)")
        # exits by time (CRT-R56) and no weekend holds (CRT-R67)
        exit_at = None
        if cfg.targets.time_exit == "end_of_htf_candle" and s.c3_close_ns is not None:
            exit_at = s.c3_close_ns
        flat = _friday_flat_ns(now, cfg.risk.friday_flat_time) if cfg.risk.no_weekend_holds else None
        if flat is not None:
            exit_at = flat if exit_at is None else min(exit_at, flat)
        expiry = s.expiry_ns
        kind = "market" if sig.order == "market" else "limit"
        try:
            order = Order(side, stop=float(stop), target=float(target), kind=kind,
                          price=float(price_ref) if kind == "limit" else None,
                          expiry=ts(expiry) if expiry else None, exit_at=ts(exit_at) if exit_at else None,
                          tag=s.id, tp1=float(tp1) if tp1 is not None else None,
                          tp1_fraction=cfg.targets.tp1_fraction if tp1 is not None else 0.0)
        except ValueError as exc:
            s.log("F", "order_valid", "fail", None, str(exc))
            s.state, s.invalid_reason = "invalidated", "order_invalid"
            return []
        if kind == "market":
            last = md.last_price()
            if (stop >= last if d == BULL else stop <= last) or (target <= last if d == BULL else target >= last):
                s.log("F", "order_valid", "fail", None, "price already beyond stop/target")
                s.state, s.invalid_reason = "invalidated", "order_invalid"
                return []
        s.entry_kind, s.order_kind = sig.kind, kind
        s.stop, s.tp1, s.target = float(stop), tp1, float(target)
        s.entry_price = float(price_ref)
        s.log("F", "order_sent", "pass", sig.kind)
        self._current = s
        self._entries_seen = state.entries_total
        return [order]

    def _fvg_fill_stop(self, md: MarketData, d: str) -> float | None:
        """CRT-R52: low of the bars that filled the most recent daily bullish FVG."""
        from crt_robot.primitives.fvg import detect_fvgs
        db = md.bars("D").tail(60)
        if len(db) < 5:
            return None
        f = detect_fvgs(db.df())
        want = "bull" if d == BULL else "bear"
        f = f[(f.kind == want) & (f.touched_idx >= 0)]
        if f.empty:
            return None
        r = f.iloc[-1]
        seg = db.slice(slice(int(r.touched_idx), len(db)))
        return float(seg.low.min()) if d == BULL else float(seg.high.max())

    # ------------------------------------------------------------------
    # open trade management (groups H, I)
    # ------------------------------------------------------------------
    def _manage_trade(self, md: MarketData, state: StrategyState) -> list:
        cfg = self.cfg
        s = self._current
        pos = state.position
        if s is None or pos is None:
            return []
        out: list = []
        if cfg.targets.be_after_tp1 and pos.tp1_done and not self._be_done:
            self._be_done = True
            s.log("CRT-R68", "breakeven_after_tp1", "info", pos.entry)
            out.append(ModifyStop(pos.entry, "be_after_tp1"))
        ltf = md.bars(s.ltf)
        key = ("mgmt_n", s.id)
        if self._cache.get(key) == len(ltf):
            return out
        self._cache[key] = len(ltf)
        # CRT-R58: closes beyond the key (sweep) extreme
        ext = s.sweep_extreme
        if ext is not None and s.entry_ns is not None:
            path = ltf.since(s.entry_ns)
            if len(path):
                rng = np.maximum(path.high - path.low, 1e-12)
                body = np.abs(path.close - path.open) / rng
                beyond = (path.close < ext) if s.direction == BULL else (path.close > ext)
                n = int((beyond & (body >= 0.5)).sum())
                if n >= cfg.invalidation.decisive_closes:
                    s.log("CRT-R58", "decisive_close_in_trade", "fail", n)
                    s.invalid_reason = "decisive_close_beyond"
                    return out + [ClosePosition("decisive_close_beyond")]
                if n >= 1 and not self._warned:
                    self._warned = True
                    s.log("CRT-R58", "first_close_beyond", "info", cfg.invalidation.on_first_close_beyond)
                    if cfg.invalidation.on_first_close_beyond == "breakeven":
                        out.append(ModifyStop(pos.entry, "first_close_beyond"))
        # CRT-R57: confirmed opposing SMT cancels the target
        if cfg.invalidation.on_opposing_smt != "ignore":
            for o in self.setups[-6:]:
                if o.direction == s.direction or o.detected_ns <= (s.entry_ns or 0) or o.htf != s.htf:
                    continue
                smt = o.check("smt")
                if smt is None or smt.status != "score" or not smt.value:
                    continue
                confirmed = self._opposing_confirmed(md, o)
                if confirmed and not s.extra.get("opp_smt_done"):
                    s.extra["opp_smt_done"] = True
                    s.log("CRT-R57", "opposing_smt", "fail", o.id)
                    if cfg.invalidation.on_opposing_smt == "close":
                        s.invalid_reason = "opposing_smt"
                        return out + [ClosePosition("opposing_smt")]
                    out.append(ModifyStop(pos.entry, "opposing_smt"))
        return out

    def _opposing_confirmed(self, md: MarketData, o: Setup) -> bool:
        if o.c2_open_ns is None or o.c2_close_ns is None:
            return False
        ltf = md.bars(o.ltf)
        hist = ltf.tail(len(ltf.since(o.c2_open_ns)) + 200)
        r1 = entries.model1(hist, o.direction, o.swept_extreme, o.c2_open_ns, o.c2_close_ns, md.now_ns, self.cfg, 0.0)
        if "trigger_ns" in r1.info:
            return True
        r2 = entries.mss_ote(hist, o.direction, o.swept_extreme, o.c2_open_ns, self.cfg, 0.0)
        return "mss_ns" in r2.info

    # ------------------------------------------------------------------
    def setups_frame(self) -> pd.DataFrame:
        from crt_robot.crt.setup import setups_frame
        return setups_frame(self.setups)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

_RANK = {"15m": 0, "1H": 1, "4H": 2, "D": 3, "W": 4, "M": 5}


def _tf_rank(tf: str) -> int:
    return _RANK.get(tf, 0)


def _week_key(ns: int) -> tuple[int, int]:
    iso = ny(ns).isocalendar()
    return (iso[0], iso[1])


def _h4_open(ns: int) -> int:
    t = ny(ns)
    h = t.hour
    oh = (h - ((h - 1) % 4)) % 24
    o = t.normalize() + pd.Timedelta(hours=oh)
    if o > t:
        o -= pd.Timedelta(days=1)
    return int(o.tz_convert("UTC").value)


def _next_killzone_end(ns: int, cfg: StrategyConfig) -> int:
    """End of the first killzone that ends after ``ns`` (CRT-R37 sham expiry)."""
    t = ny(ns)
    best = None
    for _, (a, b) in cfg.timing.killzones.items():
        end = t.normalize() + pd.Timedelta(minutes=ctx._mins(b))
        if ctx._mins(b) <= ctx._mins(a):
            end += pd.Timedelta(days=1)
        while end <= t:
            end += pd.Timedelta(days=1)
        best = end if best is None or end < best else best
    return int(best.tz_convert("UTC").value)


def _friday_flat_ns(ns: int, hhmm: str) -> int:
    """The next Friday ``hhmm`` NY at or after ``ns`` (CRT-R67 flat time)."""
    t = ny(ns)
    days = (4 - t.day_of_week) % 7
    f = (t.normalize() + pd.Timedelta(days=days) + pd.Timedelta(minutes=ctx._mins(hhmm)))
    if f <= t:
        f += pd.Timedelta(days=7)
    return int(f.tz_convert("UTC").value)
