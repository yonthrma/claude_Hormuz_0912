# -*- coding: utf-8 -*-
"""
사건데이터의 큰 CSV 를 코드로 세어, 보고서에 쓰는 숫자를 전부 여기서 뽑는다.
눈대중 금지. 결과는 분석/결과_사실재구성.json 에 저장하고 화면에도 요약을 찍는다.

    python 분석/사실재구성.py [사건데이터_경로]

표준 라이브러리만 쓴다 (csv, math, json).
"""
import csv, json, math, os, sys
from collections import defaultdict
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "사건데이터")
OUT = os.path.join(HERE, "결과_사실재구성.json")

def P(*parts):
    return os.path.join(DATA, *parts)

def ts(s):
    s = s.strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    raise ValueError(f"시각 형식 불명: {s!r}")

R = {}  # 결과 모음

# ────────────────────────────────────────────────────────────────
# 0. 거리 도구 — 위경도를 NM 평면으로 (기준 위도 26.5N). 50NM 범위라 충분.
# ────────────────────────────────────────────────────────────────
LAT0 = 26.5
COS0 = math.cos(math.radians(LAT0))

def to_nm(lat, lon):
    return (lon * 60.0 * COS0, lat * 60.0)  # (x=동서, y=남북) NM

def dist_nm(lat1, lon1, lat2, lon2):
    # 하버사인, 지구 반지름 3440.065 NM
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 3440.065 * math.asin(math.sqrt(a))

def dm_to_deg(deg, minutes):
    return deg + minutes / 60.0

# 항해계획서.md 웨이포인트 (호르무즈 구간) — 원문 그대로 옮김
WP = [
    ("WP-06", dm_to_deg(26, 14.7), dm_to_deg(56, 37.8)),
    ("WP-07", dm_to_deg(26, 21.2), dm_to_deg(56, 28.4)),
    ("WP-08", dm_to_deg(26, 28.9), dm_to_deg(56, 17.1)),
    ("WP-09", dm_to_deg(26, 36.4), dm_to_deg(56, 5.3)),
    ("WP-10", dm_to_deg(26, 44.0), dm_to_deg(55, 52.8)),
]
WP_XY = [to_nm(la, lo) for _, la, lo in WP]

def xtd_to_route(lat, lon):
    """계획 항로(폴리라인)까지의 부호 있는 최단 거리(NM).
    + 는 진행방향 기준 우현(이 항로에서는 북쪽=이란 쪽), - 는 좌현."""
    px, py = to_nm(lat, lon)
    best = None
    for i in range(len(WP_XY) - 1):
        ax, ay = WP_XY[i]
        bx, by = WP_XY[i + 1]
        vx, vy = bx - ax, by - ay
        L2 = vx * vx + vy * vy
        t = max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / L2))
        cx, cy = ax + t * vx, ay + t * vy
        d = math.hypot(px - cx, py - cy)
        cross = vx * (py - ay) - vy * (px - ax)   # >0 이면 진행방향 좌측
        signed = -d if cross > 0 else d           # 우현(+) / 좌현(-)
        if best is None or d < abs(best[0]):
            best = (signed, WP[i][0], WP[i + 1][0])
    return best

# ────────────────────────────────────────────────────────────────
# 1. 항적_HANBADA3.csv
# ────────────────────────────────────────────────────────────────
track = []
with open(P("운항로그", "항적_HANBADA3.csv"), encoding="utf-8") as f:
    rd = csv.DictReader(f)
    cols = rd.fieldnames
    for r in rd:
        track.append((ts(r["utc_kst"]), float(r["lat"]), float(r["lon"]),
                      float(r["sog_kn"]), float(r["hdg_deg"]), float(r["cog_deg"]), r["nav_mode"]))
by_time = {t[0]: t for t in track}
R["항적"] = {
    "파일": "운항로그/항적_HANBADA3.csv", "열": cols, "행수": len(track),
    "시작": str(track[0][0]), "끝": str(track[-1][0]),
    "간격초": (track[1][0] - track[0][0]).total_seconds(),
}

# 1-1 nav_mode 전환
modes = []
for i in range(1, len(track)):
    if track[i][6] != track[i - 1][6]:
        modes.append({"시각": str(track[i][0]), "from": track[i - 1][6], "to": track[i][6]})
R["항적"]["nav_mode_전환"] = modes

# 1-2 주요 시각의 위치·침로·속력·계획항로 이탈
KEY = ["2026-09-11 18:00:00", "2026-09-11 20:14:09", "2026-09-11 22:40:00", "2026-09-11 23:12:00",
       "2026-09-11 23:29:00", "2026-09-11 23:29:01", "2026-09-11 23:31:59", "2026-09-11 23:32:05",
       "2026-09-11 23:33:00", "2026-09-11 23:34:00", "2026-09-11 23:41:00", "2026-09-11 23:47:00",
       "2026-09-11 23:52:00", "2026-09-11 23:58:00", "2026-09-12 00:04:00", "2026-09-12 00:04:41",
       "2026-09-12 00:50:00", "2026-09-12 00:58:00", "2026-09-12 01:20:00"]
keyrows = []
for k in KEY:
    t = by_time.get(ts(k))
    if not t:
        keyrows.append({"시각": k, "없음": True}); continue
    x = xtd_to_route(t[1], t[2])
    keyrows.append({"시각": k, "lat": round(t[1], 5), "lon": round(t[2], 5), "sog": t[3], "hdg": t[4],
                    "cog": t[5], "mode": t[6], "계획항로이탈NM_우현+": round(x[0], 3), "구간": f"{x[1]}→{x[2]}"})
R["항적"]["주요시각"] = keyrows

# 1-3 침로 변경 시점 — 23:31:50~23:33:00 의 hdg
hdg_win = [{"시각": str(t[0]), "hdg": t[4], "cog": t[5]} for t in track
           if ts("2026-09-11 23:31:50") <= t[0] <= ts("2026-09-11 23:33:00") and t[0].second % 10 == 0]
R["항적"]["침로변경_구간_10초간격"] = hdg_win

# 1-4 계획 항로 이탈이 문턱을 넘은 첫 시각 (22:00 이후)
thresholds = [0.25, 0.5, 1.0, 2.0, 3.0]
first_cross = {}
for t in track:
    if t[0] < ts("2026-09-11 22:00:00"): continue
    x = xtd_to_route(t[1], t[2])[0]
    for th in thresholds:
        if th not in first_cross and x >= th:
            first_cross[th] = str(t[0])
R["항적"]["계획항로_우현이탈_첫시각"] = {str(k): v for k, v in first_cross.items()}
# 최대 이탈 (수동 전환 전까지)
mx = max(((xtd_to_route(t[1], t[2])[0], t[0]) for t in track if t[0] <= ts("2026-09-12 01:20:00")), key=lambda a: a[0])
R["항적"]["최대_우현이탈_0120까지"] = {"NM": round(mx[0], 3), "시각": str(mx[1])}

# 1-5 연속 위치 점프 (1초 간격에서 0.1NM 이상 = 비정상)
jumps = []
for i in range(1, len(track)):
    d = dist_nm(track[i - 1][1], track[i - 1][2], track[i][1], track[i][2])
    if d >= 0.1:
        jumps.append({"시각": str(track[i][0]), "점프NM": round(d, 3),
                      "from": [round(track[i-1][1], 5), round(track[i-1][2], 5)],
                      "to": [round(track[i][1], 5), round(track[i][2], 5)]})
R["항적"]["위치점프_0.1NM이상"] = jumps

# 1-6 정선 — sog 가 0.5kn 아래로 처음 내려간 시각 (00:00 이후)
stop = next((t for t in track if t[0] >= ts("2026-09-12 00:00:00") and t[3] < 0.5), None)
R["항적"]["정선_첫시각_sog<0.5"] = str(stop[0]) if stop else None

# ────────────────────────────────────────────────────────────────
# 2. 위성수신_HANBADA3.csv
# ────────────────────────────────────────────────────────────────
gnss = []
with open(P("운항로그", "위성수신_HANBADA3.csv"), encoding="utf-8") as f:
    rd = csv.DictReader(f)
    gcols = rd.fieldnames
    for r in rd:
        gnss.append((ts(r["utc_kst"]), int(r["sats_used"]), float(r["hdop"]), float(r["avg_snr_dbhz"]),
                     int(r["interference_level"]), r["constellation"]))
R["위성수신"] = {"파일": "운항로그/위성수신_HANBADA3.csv", "열": gcols, "행수": len(gnss),
              "시작": str(gnss[0][0]), "끝": str(gnss[-1][0])}

def stats(rows):
    if not rows: return None
    s = [r[1] for r in rows]; h = [r[2] for r in rows]; n = [r[3] for r in rows]; i = [r[4] for r in rows]
    return {"n": len(rows), "sats_평균": round(sum(s)/len(s), 2), "sats_최소": min(s),
            "hdop_평균": round(sum(h)/len(h), 2), "hdop_최대": max(h),
            "snr_평균": round(sum(n)/len(n), 1), "snr_최소": min(n), "interf_최대": max(i),
            "interf_분포": dict(sorted(((k, i.count(k)) for k in set(i))))}

R["위성수신"]["기준구간_1800_2300"] = stats([g for g in gnss if g[0] < ts("2026-09-11 23:00:00")])
R["위성수신"]["교란구간_2312_0058"] = stats([g for g in gnss if ts("2026-09-11 23:12:00") <= g[0] <= ts("2026-09-12 00:58:00")])
# 분 단위 (23:00 ~ 00:10)
per_min = defaultdict(list)
for g in gnss:
    if ts("2026-09-11 23:00:00") <= g[0] <= ts("2026-09-12 00:10:00"):
        per_min[g[0].strftime("%H:%M")].append(g)
R["위성수신"]["분단위_2300_0010"] = {k: {"sats_평균": round(sum(x[1] for x in v)/len(v), 1), "sats_최소": min(x[1] for x in v),
                                    "hdop_최대": max(x[2] for x in v), "snr_평균": round(sum(x[3] for x in v)/len(v), 1),
                                    "snr_최소": min(x[3] for x in v), "interf_최대": max(x[4] for x in v)}
                                for k, v in sorted(per_min.items())}
first_interf = next((g for g in gnss if g[4] > 0), None)
first_sats8 = next((g for g in gnss if g[0] >= ts("2026-09-11 22:00:00") and g[1] <= 8), None)
last_interf = None
for g in gnss:
    if g[4] > 0: last_interf = g
R["위성수신"]["interference>0_첫시각"] = str(first_interf[0]) if first_interf else None
R["위성수신"]["interference>0_마지막시각"] = str(last_interf[0]) if last_interf else None
R["위성수신"]["sats<=8_첫시각_2200이후"] = str(first_sats8[0]) if first_sats8 else None
mn = min(gnss, key=lambda g: g[3])
R["위성수신"]["snr_최저"] = {"값": mn[3], "시각": str(mn[0])}

# ────────────────────────────────────────────────────────────────
# 3. 주기관_HANBADA3.csv — 정선 시각 (rpm)
# ────────────────────────────────────────────────────────────────
eng_n = 0; rpm0 = None; rpm_at = {}
with open(P("운항로그", "주기관_HANBADA3.csv"), encoding="utf-8") as f:
    rd = csv.DictReader(f)
    ecols = rd.fieldnames
    for r in rd:
        eng_n += 1
        t = ts(r["utc_kst"])
        if rpm0 is None and t >= ts("2026-09-12 00:00:00") and float(r["rpm"]) < 1.0:
            rpm0 = t
        if r["utc_kst"] in ("2026-09-11 23:32:00", "2026-09-12 00:50:00", "2026-09-12 00:58:00", "2026-09-12 01:00:00"):
            rpm_at[r["utc_kst"]] = {"rpm": float(r["rpm"]), "load": float(r["load_pct"])}
R["주기관"] = {"파일": "운항로그/주기관_HANBADA3.csv", "열": ecols, "행수": eng_n,
             "rpm<1_첫시각_0000이후": str(rpm0) if rpm0 else None, "주요시각": rpm_at}

# ────────────────────────────────────────────────────────────────
# 4. AIS주변선.csv — 누가 언제 가까웠나
# ────────────────────────────────────────────────────────────────
ais_n = 0
vessels = {}   # name -> {type, mmsi, first, last, min_cpa, min_cpa_time, first_within_3nm}
ais_types = defaultdict(int)
with open(P("운항로그", "AIS주변선.csv"), encoding="utf-8") as f:
    rd = csv.DictReader(f)
    acols = rd.fieldnames
    for r in rd:
        ais_n += 1
        t = ts(r["utc_kst"]); name = r["name"]; cpa = float(r["cpa_nm"])
        v = vessels.setdefault(name, {"type": r["type"], "mmsi": r["mmsi"], "first": t, "last": t,
                                      "min_cpa": cpa, "min_cpa_time": t, "first_within_3nm": None, "n": 0})
        v["n"] += 1; v["last"] = t
        if cpa < v["min_cpa"]: v["min_cpa"], v["min_cpa_time"] = cpa, t
        if cpa <= 3.0 and v["first_within_3nm"] is None: v["first_within_3nm"] = t
        ais_types[r["type"]] += 1
R["AIS"] = {"파일": "운항로그/AIS주변선.csv", "열": acols, "행수": ais_n, "선박수": len(vessels),
           "유형별행수": dict(ais_types),
           "선박별": {k: {"type": v["type"], "mmsi": v["mmsi"], "첫기록": str(v["first"]), "마지막": str(v["last"]),
                        "행수": v["n"], "최소CPA_NM": v["min_cpa"], "최소CPA시각": str(v["min_cpa_time"]),
                        "CPA<=3NM_첫시각": str(v["first_within_3nm"]) if v["first_within_3nm"] else None}
                    for k, v in sorted(vessels.items(), key=lambda kv: kv[1]["min_cpa"])}}

# ────────────────────────────────────────────────────────────────
# 5. VHF 23:47 호출 좌표와 우리 위치 비교
# ────────────────────────────────────────────────────────────────
hail_lat, hail_lon = dm_to_deg(26, 32.0), dm_to_deg(56, 15.0)
t2347 = by_time[ts("2026-09-11 23:47:00")]
R["VHF_2347_호출좌표"] = {"호출좌표": [hail_lat, hail_lon], "우리기록위치": [round(t2347[1], 5), round(t2347[2], 5)],
                      "거리NM": round(dist_nm(hail_lat, hail_lon, t2347[1], t2347[2]), 2),
                      "비고": "우리 기록 위치는 스푸핑 영향을 받은 값일 수 있음. 실제 위치는 이 파일로 확정 불가"}

# ────────────────────────────────────────────────────────────────
# 6. 이전항차 — 5월(HB-2427 '1.1NM 점프'), 8월
# ────────────────────────────────────────────────────────────────
def prev_voyage(tag):
    tr = []
    with open(P("이전항차", f"항적_HANBADA3_{tag}.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            tr.append((ts(r["utc_kst"]), float(r["lat"]), float(r["lon"]), float(r["hdg_deg"]), r["nav_mode"]))
    js = []
    for i in range(1, len(tr)):
        d = dist_nm(tr[i-1][1], tr[i-1][2], tr[i][1], tr[i][2])
        if d >= 0.1: js.append({"시각": str(tr[i][0]), "점프NM": round(d, 3)})
    hchg = []
    for i in range(1, len(tr)):
        dh = abs(tr[i][3] - tr[i-1][3]); dh = min(dh, 360 - dh)
        if dh >= 5: hchg.append({"시각": str(tr[i][0]), "from": tr[i-1][3], "to": tr[i][3]})
    mxx = max(((xtd_to_route(t[1], t[2])[0], t[0]) for t in tr), key=lambda a: a[0])
    gn = []
    with open(P("이전항차", f"위성수신_HANBADA3_{tag}.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            gn.append((ts(r["utc_kst"]), int(r["sats_used"]), float(r["hdop"]), float(r["avg_snr_dbhz"]), int(r["interference_level"])))
    interf = [g for g in gn if g[4] > 0]
    return {"항적행수": len(tr), "시작": str(tr[0][0]), "끝": str(tr[-1][0]),
            "위치점프_0.1NM이상": js, "침로변경_5도이상": hchg[:10], "침로변경_건수": len(hchg),
            "최대_우현이탈": {"NM": round(mxx[0], 3), "시각": str(mxx[1])},
            "nav_mode_집합": sorted(set(t[4] for t in tr)),
            "위성수신행수": len(gn), "interference>0_구간": [str(interf[0][0]), str(interf[-1][0])] if interf else None,
            "interference>0_행수": len(interf), "sats_최소": min(g[1] for g in gn), "snr_최소": min(g[3] for g in gn)}
R["이전항차_202605"] = prev_voyage("202605")
R["이전항차_202608"] = prev_voyage("202608")

# ────────────────────────────────────────────────────────────────
# 7. 시스템이벤트 / 원격관제기록 — 간격 계산
# ────────────────────────────────────────────────────────────────
ev = list(csv.DictReader(open(P("운항로그", "시스템이벤트.csv"), encoding="utf-8")))
evt = {e["code"]: ts(e["utc_kst"]) for e in ev}
R["시스템이벤트"] = {"행수": len(ev),
    "NAV-0300_재계산→CTRL-5002_타임아웃_초": (evt["CTRL-5002"] - evt["NAV-0300"]).total_seconds(),
    "GEO-6001_접근→GEO-6002_통과_분": (evt["GEO-6002"] - evt["GEO-6001"]).total_seconds() / 60,
    "GNSS-3001_첫경고→NAV-0300_재계산_분": (evt["NAV-0300"] - evt["GNSS-3001"]).total_seconds() / 60,
    "NAV-0300_재계산→SYS-0190_수동전환_분": (evt["SYS-0190"] - evt["NAV-0300"]).total_seconds() / 60,
    "GNSS-3010_스푸핑경보→SYS-0190_수동전환_분": (evt["SYS-0190"] - evt["GNSS-3010"]).total_seconds() / 60,
    "action_값": sorted(set(e["action"] for e in ev if e["action"])),
    "alert_only_건": [f'{e["utc_kst"]} {e["code"]}' for e in ev if e["action"] == "alert_only"]}
rc = list(csv.DictReader(open(P("운항로그", "원격관제기록.csv"), encoding="utf-8")))
R["원격관제기록"] = {"행수": len(rc), "action_값": sorted(set(r["action"] for r in rc)),
                 "승인(APPROVE)행": [r for r in rc if "APPROV" in r["action"].upper()],
                 "23:32~23:34_사이_행": [r for r in rc if ts("2026-09-11 23:32:00") <= ts(r["utc_kst"]) <= ts("2026-09-11 23:34:00")],
                 "23:36_NOTE": [r for r in rc if r["utc_kst"] == "2026-09-11 23:36:00"],
                 "GNSS경고(23:12)→ACK(23:13)_분": (ts("2026-09-11 23:13:00") - evt["GNSS-3001"]).total_seconds() / 60,
                 "스푸핑경보(23:29)→ACK(23:31)_분": (ts("2026-09-11 23:31:00") - evt["GNSS-3010"]).total_seconds() / 60,
                 "재계산(23:32)→책임자호출(23:45)_분": (ts("2026-09-11 23:45:00") - evt["NAV-0300"]).total_seconds() / 60,
                 "재계산(23:32)→수동전환지시(00:55)_분": (ts("2026-09-12 00:55:00") - evt["NAV-0300"]).total_seconds() / 60}

# ────────────────────────────────────────────────────────────────
# 8. 근무기록 / 보험 통보 이력 — 작은 CSV 도 코드로
# ────────────────────────────────────────────────────────────────
duty = list(csv.DictReader(open(P("관제센터", "근무기록_20260911.csv"), encoding="utf-8")))
R["근무기록"] = {"행수": len(duty), "행": duty,
              "이승주_연속야간_0911": [d for d in duty if d["날짜"] == "2026-09-11"][0]["연속근무일"],
              "이승주_휴식시간_추이": [(d["날짜"], d["교대전_휴식시간(h)"]) for d in duty if d["관제사"] == "이승주"]}
ins = list(csv.DictReader(open(P("재무", "전쟁위험보험_통보이력.csv"), encoding="utf-8")))
ins_rows = []
for r in ins:
    if r["통보일시"]:
        h = (ts(r["진입예정일시"]) - ts(r["통보일시"])).total_seconds() / 3600
        ins_rows.append({"항차": r["항차"], "재계산_경과h": round(h, 1), "파일값": r["통보경과시간(h)"], "72h충족": h >= 72, "담당": r["담당"]})
    else:
        ins_rows.append({"항차": r["항차"], "재계산_경과h": None, "파일값": "", "72h충족": False, "담당": r["담당"], "비고": "통보 기록 없음"})
R["전쟁위험보험_통보"] = {"행수": len(ins), "항차별": ins_rows,
                     "72h_미충족_항차": [x["항차"] for x in ins_rows if not x["72h충족"]]}

# ────────────────────────────────────────────────────────────────
# 9. 보조 수치 — 주장 검증용
# ────────────────────────────────────────────────────────────────
gby = {g[0]: g for g in gnss}
def grow(k):
    g = gby.get(ts(k))
    return {"sats": g[1], "hdop": g[2], "snr": g[3], "interf": g[4]} if g else None
R["위성수신"]["경계행"] = {k: grow(k) for k in ("2026-09-11 23:11:59", "2026-09-11 23:12:00", "2026-09-11 23:28:59",
                                             "2026-09-11 23:29:00", "2026-09-12 00:57:59", "2026-09-12 00:58:00")}
# 개발1팀 메일 주장 "위성 14→8, SNR 42→24" 와 대조: 23:00~23:11 최대 sats / 23:12~23:28 sats·snr 범위
pre = [g for g in gnss if ts("2026-09-11 23:00:00") <= g[0] < ts("2026-09-11 23:12:00")]
lv1 = [g for g in gnss if ts("2026-09-11 23:12:00") <= g[0] < ts("2026-09-11 23:29:00")]
R["위성수신"]["주장대조_개발1팀"] = {
    "23:00~23:11_sats_범위": [min(g[1] for g in pre), max(g[1] for g in pre)],
    "23:12~23:28_sats_범위": [min(g[1] for g in lv1), max(g[1] for g in lv1)],
    "23:00~23:11_snr_범위": [min(g[3] for g in pre), max(g[3] for g in pre)],
    "23:12~23:28_snr_범위": [min(g[3] for g in lv1), max(g[3] for g in lv1)],
    "메일주장": "위성 14→8, SNR 42dB→24dB (사내/메일_20260912_개발1팀.md)"}

# 23:32~00:58 항적: 선회량·이동거리·속력 범위 (감속했나)
seg = [t for t in track if ts("2026-09-11 23:32:00") <= t[0] <= ts("2026-09-12 00:58:00")]
dist_sum = sum(dist_nm(seg[i-1][1], seg[i-1][2], seg[i][1], seg[i][2]) for i in range(1, len(seg)))
R["항적"]["재계산후_수동전환까지"] = {
    "구간": "23:32:00 ~ 00:58:00", "시간_분": 86,
    "hdg_시작": seg[0][4], "hdg_끝": seg[-1][4], "선회량_도(우현)": round((seg[-1][4] - seg[0][4]) % 360, 1),
    "이동거리_NM(항적합)": round(dist_sum, 2),
    "직선거리_NM": round(dist_nm(seg[0][1], seg[0][2], seg[-1][1], seg[-1][2]), 2),
    "sog_최소": min(t[3] for t in seg), "sog_최대": max(t[3] for t in seg),
    "비고": "sog 최소가 13kn 대면 경보·호출 뒤에도 감속하지 않은 것"}
# 정선 명령(00:04 선명 호출) → 기관 정지(00:58) → 정선(sog<0.5)
R["항적"]["정선까지_분"] = {"00:04_선명호출→00:58_기관정지": 54, "23:52_변침요구→00:58": 66,
                        "00:58_기관정지→sog<0.5": round((ts(R["항적"]["정선_첫시각_sog<0.5"]) - ts("2026-09-12 00:58:00")).total_seconds() / 60, 1)}

# 항해경보(NAVWARN) 박스 26-10N~26-50N, 056-00E~057-00E 안에 우리 기록 위치가 있었나
def in_box(lat, lon): return 26 + 10/60 <= lat <= 26 + 50/60 and 56.0 <= lon <= 57.0
R["항적"]["NAVWARN박스_안에_있던_기록시각"] = {
    "박스": "26-10N~26-50N, 056-00E~057-00E (외부/통지_20260912_항만당국.md)",
    "18:00": in_box(track[0][1], track[0][2]),
    "박스_벗어난_첫시각": next((str(t[0]) for t in track if not in_box(t[1], t[2])), None),
    "23:12": in_box(*by_time[ts("2026-09-11 23:12:00")][1:3]),
    "23:32": in_box(*by_time[ts("2026-09-11 23:32:00")][1:3]),
    "비고": "기록 위치 기준. 실제 위치와 다를 수 있음"}

# 5월 항차 침로 변화 (2도 문턱) — HB-2428 '원격 승인 없이 침로 변경' 과 대조
tr5 = []
with open(P("이전항차", "항적_HANBADA3_202605.csv"), encoding="utf-8") as f:
    for r in csv.DictReader(f):
        tr5.append((ts(r["utc_kst"]), float(r["hdg_deg"])))
h5 = [t[1] for t in tr5]
R["이전항차_202605"]["hdg_범위"] = [min(h5), max(h5)]
R["이전항차_202605"]["hdg_분평균_2200_2230"] = {}
pm = defaultdict(list)
for t in tr5:
    if ts("2026-05-22 21:50:00") <= t[0] <= ts("2026-05-22 22:40:00"): pm[t[0].strftime("%H:%M")].append(t[1])
R["이전항차_202605"]["hdg_분평균_2150_2240"] = {k: round(sum(v)/len(v), 1) for k, v in sorted(pm.items()) if k.endswith(("0", "5"))}

# ────────────────────────────────────────────────────────────────
# 저장 + 요약 출력
# ────────────────────────────────────────────────────────────────
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(R, f, ensure_ascii=False, indent=1, default=str)

def show(title, obj):
    print(f"\n### {title}")
    print(json.dumps(obj, ensure_ascii=False, indent=1, default=str))

show("항적 개요", {k: v for k, v in R["항적"].items() if k in ("행수", "시작", "끝", "간격초", "nav_mode_전환", "계획항로_우현이탈_첫시각", "최대_우현이탈_0120까지", "위치점프_0.1NM이상", "정선_첫시각_sog<0.5")})
show("항적 주요시각", R["항적"]["주요시각"])
show("침로변경 구간", R["항적"]["침로변경_구간_10초간격"])
show("위성수신", {k: v for k, v in R["위성수신"].items() if k != "분단위_2300_0010"})
show("위성수신 분단위(23:05~23:40 일부)", {k: v for k, v in R["위성수신"]["분단위_2300_0010"].items() if "23:05" <= k <= "23:40"})
show("주기관", R["주기관"])
show("AIS 선박별 (CPA 작은 순 8척)", dict(list(R["AIS"]["선박별"].items())[:8]))
show("AIS 개요", {k: v for k, v in R["AIS"].items() if k != "선박별"})
show("VHF 23:47", R["VHF_2347_호출좌표"])
show("이전항차 5월", R["이전항차_202605"])
show("이전항차 8월", R["이전항차_202608"])
show("시스템이벤트 간격", R["시스템이벤트"])
show("원격관제기록", R["원격관제기록"])
show("근무기록", {k: v for k, v in R["근무기록"].items() if k != "행"})
show("전쟁위험보험 통보", R["전쟁위험보험_통보"])
show("보조: 위성수신 경계행·주장대조", {"경계행": R["위성수신"]["경계행"], "주장대조": R["위성수신"]["주장대조_개발1팀"]})
show("보조: 재계산후~수동전환", R["항적"]["재계산후_수동전환까지"])
show("보조: 정선까지", R["항적"]["정선까지_분"])
show("보조: NAVWARN 박스", R["항적"]["NAVWARN박스_안에_있던_기록시각"])
show("보조: 5월 항차 침로", {"hdg_범위": R["이전항차_202605"]["hdg_범위"], "분평균": R["이전항차_202605"]["hdg_분평균_2150_2240"]})
print(f"\n저장: {OUT}")
