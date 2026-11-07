"""Vietnamese display helpers; no scheduling decisions are made here."""

from html import escape

import plotly.graph_objects as go

from application.models import DAY_LABELS, DAYS, TIMES, WINDOWS

SAMPLE_LABELS = {
    "Basic": "Cơ bản · 8 buổi, 3 phòng",
    "Congestion": "Tải tập trung · 24 buổi, 6 phòng",
    "Saturday trade-off": "Đánh đổi thứ Bảy · 4 buổi, 1 phòng",
    "Infeasible": "Không khả thi · 3 buổi, 2 phòng",
}
WINDOW_LABELS = {"Morning": "Đầu ngày", "1→2": "Ca 1 → 2", "2→3": "Ca 2 → 3", "3→4": "Ca 3 → 4", "Evening": "Cuối ngày"}
WINDOW_TIMES = {"Morning": "Trước 07:00", "1→2": "09:30–10:00", "2→3": "12:30–13:30", "3→4": "16:00–16:30", "Evening": "Sau 19:00"}
ROOM_PALETTE = (("#e8f0fd", "#456eb2"), ("#eee9fa", "#8060ac"), ("#e1f2ec", "#27846b"), ("#fff0dd", "#b1792f"), ("#fbe8ed", "#b35c76"), ("#e4f2f8", "#407e9b"), ("#edf0e1", "#7b893c"), ("#efebea", "#846c62"))
STATUS_LABELS = {
    "OPTIMAL": "Đã chứng minh tối ưu", "FEASIBLE": "Đã có lịch hợp lệ",
    "INFEASIBLE": "Không có lịch khả thi", "UNKNOWN": "Chưa có kết luận",
    "MODEL_INVALID": "Mô hình không hợp lệ", "FAILED": "Chưa xếp đủ lịch",
}


def dataset_label(name):
    return SAMPLE_LABELS.get(name, name.replace("Synthetic · seed ", "Giả lập · seed "))


def room_colors(room_ids):
    return {room: ROOM_PALETTE[i % len(ROOM_PALETTE)] for i, room in enumerate(sorted(set(room_ids)))}


def timetable_grid_html(frame, days, room_ids=None):
    """Show every assignment, including simultaneous classes in different rooms.

    Workbook text is untrusted; escape it before inserting it into the grid.
    The table scrolls inside its region on small screens and retains semantics
    for keyboard and screen-reader users.
    """
    colors = room_colors(frame.room_id if room_ids is None else room_ids)
    parts = ["""<style>
    .cf-grid { overflow-x: auto; border: 1px solid #d8e3dd; border-radius: 10px; }
    .cf-grid:focus-visible { outline: 2px solid #187566; }
    .cf-timetable { width: 100%; border-collapse: collapse; table-layout: fixed; color: #172e2b; }
    .cf-timetable th, .cf-timetable td { padding: 8px; border: 1px solid #d8e3dd; vertical-align: top; overflow-wrap: anywhere; }
    .cf-timetable thead th { background: #edf2ee; text-align: left; }
    .cf-timetable .cf-session { width: 108px; background: #f6f8f5; font-size: .9rem; }
    .cf-timetable small { color: #536963; font-weight: normal; }
    .cf-timetable .cf-saturday { background: #e7f2eb; }
    .cf-class { padding: 9px; border-left: 4px solid; border-radius: 7px; }
    .cf-class + .cf-class { margin-top: 7px; }
    .cf-slot-summary { margin-bottom: 7px; color: #38574c; font-size: .75rem; font-weight: 600; }
    .cf-class strong { display: block; font-size: .8rem; }
    .cf-class-name { font-size: .9rem; line-height: 1.35; font-weight: 600; margin: 5px 0; }
    .cf-empty { color: #74857c; }
    </style>"""]
    parts.append('<div class="cf-grid" role="region" aria-label="Lưới lịch học" tabindex="0">')
    parts.append(f'<table class="cf-timetable" aria-label="Lịch theo ngày và ca" style="min-width:{108 + 140 * len(days)}px"><thead><tr><th scope="col" class="cf-session">Ca học</th>')
    for day in days:
        css = ' class="cf-saturday"' if day == "Sat" else ""
        parts.append(f'<th scope="col"{css}>{escape(DAY_LABELS[day])}</th>')
    parts.append("</tr></thead><tbody>")
    for session, (start, end) in TIMES.items():
        parts.append(f'<tr><th scope="row" class="cf-session">Ca {session}<br><small>{start}–{end}</small></th>')
        for day in days:
            css = ' class="cf-saturday"' if day == "Sat" else ""
            parts.append(f"<td{css}>")
            rows = frame[(frame.day == day) & (frame.session_id == session)]
            if not rows.empty:
                parts.append(f'<div class="cf-slot-summary">{len(rows)} lớp · {int(rows.students.sum()):,} lượt đăng ký</div>')
            for row in rows.itertuples(index=False):
                background, border = colors[row.room_id]
                parts.append(f'<div class="cf-class" data-room="{escape(str(row.room_id), quote=True)}" style="background:{background};border-left-color:{border}"><strong>{escape(str(row.class_id))}</strong>'
                             f'<div class="cf-class-name">{escape(str(row.class_name))}</div>'
                             f'<small>{escape(str(row.room_id))} · {row.students:,} lượt</small></div>')
            if rows.empty:
                parts.append('<span class="cf-empty" aria-label="Không có buổi học">—</span>')
            parts.append("</td>")
        parts.append("</tr>")
    parts.append("</tbody></table></div>")
    return "".join(parts)


def movement_heatmap(metrics, days=DAYS):
    """Whole-week overview: exact values, relative color, no safety thresholds."""
    lookup = {(w.day, w.window): w.total for w in metrics.windows}
    values = [[lookup[day, window] for day in days] for window in WINDOWS]
    labels = [[f"{v:,} ★" if v == metrics.peak_movement and v > 0 else f"{v:,}" for v in row] for row in values]
    fig = go.Figure(go.Heatmap(
        x=[DAY_LABELS[d] for d in days], y=[f"{WINDOW_LABELS[w]}<br>{WINDOW_TIMES[w]}" for w in WINDOWS],
        z=values, text=labels, texttemplate="%{text}", textfont=dict(size=15, color="#17392e"),
        colorscale=[[0, "#f1f5f2"], [.5, "#d0e9df"], [1, "#79baa3"]],
        zmin=0, zmax=max(metrics.peak_movement, 1), showscale=False, xgap=5, ygap=5,
        hovertemplate="%{x} · %{y}<br>%{z:,} lượt đăng ký lớp<extra></extra>",
    ))
    fig.update_layout(height=330, margin=dict(t=10, r=5, b=30, l=5))
    fig.update_yaxes(autorange="reversed", automargin=True, fixedrange=True)
    fig.update_xaxes(side="top", fixedrange=True)
    return fig


def comparison_figure(greedy, cp_sat):
    if not (greedy.complete and cp_sat.complete):
        raise ValueError("Chỉ vẽ so sánh khi cả hai lịch đều hoàn chỉnh và hợp lệ.")
    fig = go.Figure()
    for result, label, color in ((greedy, "Greedy · đối chiếu", "#aebcb6"), (cp_sat, "CP-SAT", "#187566")):
        values = [result.metrics.peak_movement, result.metrics.saturday_enrollment]
        fig.add_bar(name=label, y=["Lượt cao điểm", "Lượt học thứ Bảy"], x=values, orientation="h",
                    marker_color=color, text=values, textposition="outside", cliponaxis=False,
                    hovertemplate="%{y}: %{x:,} lượt<extra>%{fullData.name}</extra>")
    fig.update_layout(barmode="group", height=240, margin=dict(l=5, r=50, t=45, b=10),
                      legend=dict(orientation="h", y=1.25), xaxis_title="Lượt đăng ký lớp")
    fig.update_yaxes(autorange="reversed", automargin=True)
    fig.update_xaxes(rangemode="tozero")
    return fig


def visual_comparison_summary(greedy, cp_sat):
    if not (greedy.complete and cp_sat.complete):
        return comparison_summary(greedy, cp_sat)
    delta = greedy.metrics.peak_movement - cp_sat.metrics.peak_movement
    if delta > 0:
        peak = f"Cao điểm giảm {delta:,} lượt ({delta / greedy.metrics.peak_movement:.1%})."
    elif delta < 0:
        peak = f"Cao điểm tăng {-delta:,} lượt."
    else:
        peak = f"Cao điểm không đổi ({cp_sat.metrics.peak_movement:,} lượt)."
    saturday_delta = greedy.metrics.saturday_enrollment - cp_sat.metrics.saturday_enrollment
    if saturday_delta:
        sat = f" Lượt học thứ Bảy {'giảm' if saturday_delta > 0 else 'tăng'} {abs(saturday_delta):,}."
    else:
        sat = " Lượt học thứ Bảy không đổi."
    return peak + sat


def busiest_day(metrics, days=DAYS):
    return max(days, key=lambda day: max(w.total for w in metrics.windows if w.day == day))


def movement_figure(metrics, day=None, days=DAYS):
    windows = [w for w in metrics.windows if w.day in days and (day is None or w.day == day)]
    labels = [WINDOW_LABELS[w.window] if day else f"{DAY_LABELS[w.day]}<br>{WINDOW_LABELS[w.window]}" for w in windows]
    fig = go.Figure()
    for attr, name, color in (("departures", "Lượt rời ca trước", "#a4c7ba"), ("arrivals", "Lượt đến ca sau", "#187566")):
        fig.add_bar(name=name, x=labels, y=[getattr(w, attr) for w in windows], marker_color=color,
                    customdata=[DAY_LABELS[w.day] for w in windows],
                    hovertemplate="%{customdata}<br>%{x}: %{y:,} lượt<extra>%{fullData.name}</extra>")
    fig.add_hline(y=metrics.peak_movement, line_dash="dot", line_color="#bd784a", annotation_text=f"Đỉnh toàn tuần P = {metrics.peak_movement:,}")
    fig.update_layout(barmode="stack", height=350 if day else 430,
                      yaxis_title="Lượt đăng ký lớp ra + vào", xaxis_title="Cửa sổ di chuyển" if day else "Ngày · Cửa sổ di chuyển",
                      legend=dict(orientation="h", y=1.18), margin=dict(t=60, b=40 if day else 100), hovermode="x unified")
    fig.update_xaxes(tickangle=0 if day else -55)
    fig.update_yaxes(rangemode="tozero")
    return fig


def result_summary(result):
    if not result.complete:
        return "Chưa có lịch hoàn chỉnh được kiểm chứng để phân tích."
    m = result.metrics
    window = next(w for w in m.windows if w.total == m.peak_movement)
    return (f"Đã xếp đủ {len(result.assignments)} buổi học. Đỉnh di chuyển là {m.peak_movement:,} lượt; "
            f"một cửa sổ đạt đỉnh nằm ở {DAY_LABELS[window.day]}, {WINDOW_LABELS[window.window].lower()}. "
            f"Thứ Bảy có {m.saturday_classes} buổi với {m.saturday_enrollment:,} lượt đăng ký lớp.")


def comparison_summary(greedy, cp_sat):
    if not cp_sat.complete:
        return "CP-SAT chưa có lịch hoàn chỉnh; chưa thể so sánh chất lượng với Greedy."
    if not greedy.complete:
        return "CP-SAT đã xếp đủ lịch, trong khi Greedy chưa xếp đủ. Không so sánh mục tiêu của lịch còn thiếu."
    g, c = greedy.metrics, cp_sat.metrics
    delta = g.objective - c.objective
    if delta > 0:
        score = f"CP-SAT giảm mục tiêu J từ {g.objective:,} xuống {c.objective:,} ({delta / g.objective:.1%}) so với Greedy."
    elif delta == 0:
        score = f"Hai thuật toán đạt cùng mục tiêu J = {c.objective:,}; lần chạy này CP-SAT chưa cải thiện J so với Greedy."
    else:
        score = f"Greedy có J = {g.objective:,}, thấp hơn CP-SAT ({c.objective:,}) trong lần chạy này."
    return f"{score} Đỉnh di chuyển P: {g.peak_movement:,} → {c.peak_movement:,}; lượt thứ Bảy: {g.saturday_enrollment:,} → {c.saturday_enrollment:,}."


def what_if_summary(results):
    complete = sorted((penalty, r) for penalty, r in results if r.complete)
    if len(complete) < 2:
        return "Cần ít nhất hai lịch hợp lệ để đối chiếu sự đánh đổi giữa các mức phạt."
    low, first = complete[0]
    high, last = complete[-1]
    a, b = first.metrics, last.metrics
    if (a.peak_movement, a.saturday_enrollment) == (b.peak_movement, b.saturday_enrollment):
        summary = f"Giữa λ = {low} và λ = {high}, đỉnh di chuyển và lượt thứ Bảy không đổi: P = {a.peak_movement:,}, N_Sat = {a.saturday_enrollment:,}."
    else:
        summary = (f"Từ λ = {low} sang λ = {high}, đỉnh di chuyển P thay đổi {a.peak_movement:,} → {b.peak_movement:,}; "
                   f"lượt đăng ký thứ Bảy thay đổi {a.saturday_enrollment:,} → {b.saturday_enrollment:,}.")
    if any(r.status == "FEASIBLE" for _, r in results if r.complete):
        summary += " Có kết quả chưa được chứng minh tối ưu."
    if len(complete) < len(results):
        summary += " Một số mức phạt chưa có lịch hợp lệ; xem trạng thái từng lần giải."
    return summary
