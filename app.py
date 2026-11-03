import time
from datetime import datetime

import pandas as pd
import streamlit as st

from models.router import DemoModel, ModelRouter
from models.real_router import RealModelRouter
from migration.lifecycle_registry import ModelLifecycleRegistry
from monitoring.monitor import log_request, read_logs


# ==========================================
# PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="AI Model Guardian",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==========================================
# CUSTOM DARK THEME
# ==========================================

st.markdown(
    """
    <style>
    @import url(
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
    );

    :root {
        --bg: #090e1a;
        --panel: #111c2f;
        --border: #26354b;
        --cyan: #29dde7;
        --text: #e8f0fa;
        --muted: #8a9bb5;
        --green: #44dca4;
        --orange: #ffb74d;
    }

    .stApp {
        background: var(--bg);
        color: var(--text);
        font-family: 'Inter', sans-serif;
    }

    [data-testid="stSidebar"] {
        background: #0b1220;
        border-right: 1px solid var(--border);
    }

    [data-testid="stSidebar"] * {
        font-family: 'Inter', sans-serif;
    }

    h1, h2, h3 {
        color: var(--text) !important;
        font-family: 'Inter', sans-serif !important;
        letter-spacing: -0.5px;
    }

    p, label, span {
        font-family: 'Inter', sans-serif;
    }

    .brand {
        font-size: 22px;
        font-weight: 800;
        line-height: 1.5;
        color: var(--text);
        padding: 8px 0 22px 0;
    }

    .brand span {
        color: var(--cyan);
    }

    .eyebrow {
        color: var(--cyan);
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 2px;
        margin-bottom: 8px;
    }

    .subtitle {
        color: var(--muted);
        font-size: 13px;
        margin-top: -10px;
        margin-bottom: 24px;
    }

    .status-pill {
        display: inline-block;
        padding: 7px 12px;
        border: 1px solid #66502c;
        background: #2b2418;
        border-radius: 8px;
        color: var(--orange);
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.5px;
    }

    .metric-card {
        background: linear-gradient(
            145deg,
            #142238,
            #101a2c
        );
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 19px;
        min-height: 132px;
        margin-bottom: 12px;
    }

    .metric-label {
        color: var(--muted);
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 1px;
        margin-bottom: 15px;
    }

    .metric-value {
        color: var(--text);
        font-size: 30px;
        font-weight: 800;
        margin-bottom: 8px;
    }

    .metric-caption {
        color: var(--muted);
        font-size: 11px;
    }

    .panel {
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 18px;
    }

    .panel-title {
        color: var(--text);
        font-size: 16px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .panel-subtitle {
        color: var(--muted);
        font-size: 11px;
        margin-bottom: 18px;
    }

    .model-card {
        background: #0d1728;
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 12px;
    }

    .model-name {
        color: var(--text);
        font-weight: 700;
        font-size: 14px;
    }

    .model-role {
        color: var(--muted);
        font-size: 10px;
        margin-top: 5px;
    }

    .healthy {
        color: var(--green);
        font-size: 11px;
        font-weight: 700;
    }

    .warning {
        color: var(--orange);
        font-size: 11px;
        font-weight: 700;
    }

    .incident {
        border-bottom: 1px solid var(--border);
        padding: 13px 0;
    }

    .incident:last-child {
        border-bottom: none;
    }

    .incident-time {
        color: var(--muted);
        font-size: 10px;
    }

    .incident-title {
        color: var(--text);
        font-size: 12px;
        font-weight: 600;
        margin-top: 5px;
    }

    .incident-description {
        color: var(--muted);
        font-size: 10px;
        margin-top: 4px;
    }

    div.stButton > button {
        background: linear-gradient(
            90deg,
            #087e91,
            #12a9b7
        );
        color: white;
        border: 1px solid #21c6d1;
        border-radius: 9px;
        font-weight: 700;
        min-height: 42px;
        transition: 0.2s;
    }

    div.stButton > button:hover {
        border-color: var(--cyan);
        color: white;
        filter: brightness(1.12);
    }

    div[data-testid="stMetric"] {
        background: #111c2f;
        border: 1px solid var(--border);
        padding: 14px;
        border-radius: 10px;
    }

    div[data-testid="stMetricLabel"] {
        color: var(--muted);
    }

    div[data-testid="stMetricValue"] {
        color: var(--text);
    }

    .stTextArea textarea {
        background: #0d1728;
        color: var(--text);
        border: 1px solid var(--border);
        border-radius: 9px;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid var(--border);
        border-radius: 10px;
    }

    hr {
        border-color: var(--border);
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def get_dataframe():
    """Load request records from the monitoring system."""

    records = read_logs()

    if not records:
        return pd.DataFrame(
            columns=[
                "timestamp",
                "model",
                "response_time_seconds",
                "status",
                "fallback_used",
                "error",
            ]
        )

    df = pd.DataFrame(records)

    df["response_time_seconds"] = pd.to_numeric(
        df["response_time_seconds"],
        errors="coerce",
    )

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce",
        utc=True,
    )

    df["fallback_used"] = (
        df["fallback_used"]
        .astype(str)
        .str.lower()
        .eq("true")
    )

    return df


def metric_card(label, value, caption, accent="#29dde7"):
    """Render a dashboard metric card."""

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value" style="color:{accent}">
                {value}
            </div>
            <div class="metric-caption">{caption}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def panel_heading(title, subtitle):
    """Render a reusable panel heading."""

    st.markdown(
        f"""
        <div class="panel-title">{title}</div>
        <div class="panel-subtitle">{subtitle}</div>
        """,
        unsafe_allow_html=True,
    )


# ==========================================
# SIDEBAR
# ==========================================

with st.sidebar:

    st.markdown(
        """
        <div class="brand">
            ◈ AI MODEL<br>
            <span>GUARDIAN</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption("WORKSPACE")

    page = st.radio(
        "Navigation",
        [
            "Overview",
            "Model Health",
            "Routing & Failover",
            "Performance",
            "Migration Center",
            "Request Logs",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")

    st.caption("ENVIRONMENT")

    use_live_providers = st.toggle(
        "Use live AI providers",
        value=False,
        help=(
            "When enabled, requests use Gemini first and OpenAI "
            "as the backup. Live API usage may incur charges."
        ),
    )

    if use_live_providers:
        st.success("LIVE MODE · Gemini → OpenAI")
        st.caption(
            "Real API calls are enabled. Requests are logged."
        )
    else:
        st.warning("DEMO MODE")
        st.caption(
            "Uses simulated models; no provider API calls are made."
        )

    st.caption("AI Model Guardian · v0.2")


df = get_dataframe()


# ==========================================
# OVERVIEW DASHBOARD
# ==========================================

if page == "Overview":

    st.markdown(
        '<div class="eyebrow">OVERVIEW / SYSTEM STATUS</div>',
        unsafe_allow_html=True,
    )

    st.title("AI Operations Dashboard")

    st.markdown(
        '<div class="subtitle">'
        'Monitor reliability, route around failures, '
        'and prepare model migrations.'
        '</div>',
        unsafe_allow_html=True,
    )

    environment_label = (
        "● LIVE API MODE ENABLED"
        if use_live_providers
        else "● SIMULATED ENVIRONMENT"
    )

    st.markdown(
        f'<div class="status-pill">{environment_label}</div>',
        unsafe_allow_html=True,
    )

    st.write("")

    total = len(df)

    successes = (
        int((df["status"] == "success").sum())
        if total else 0
    )

    failures = (
        int((df["status"] == "failed").sum())
        if total else 0
    )

    fallback_count = (
        int(df["fallback_used"].sum())
        if total else 0
    )

    success_rate = (
        successes / total * 100
        if total else 0
    )

    avg_latency = (
        df["response_time_seconds"].mean()
        if total else 0
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        metric_card(
            "TOTAL REQUESTS",
            total,
            "Recorded requests",
        )

    with c2:
        metric_card(
            "SUCCESS RATE",
            f"{success_rate:.1f}%",
            f"{successes} successful requests",
            "#44dca4",
        )

    with c3:
        metric_card(
            "AVG. LATENCY",
            f"{avg_latency * 1000:.2f} ms",
            "Measured processing time",
            "#86aaff",
        )

    with c4:
        metric_card(
            "FALLBACK EVENTS",
            fallback_count,
            f"{failures} failed requests",
            "#ffb74d",
        )

    st.write("")

    left, right = st.columns([1.35, 1])

    with left:

        st.markdown(
            '<div class="panel">',
            unsafe_allow_html=True,
        )

        panel_heading(
            "Request Performance",
            "Recorded request volume and response latency",
        )

        if not df.empty:

            chart_df = df.dropna(
                subset=["timestamp"]
            ).copy()

            if not chart_df.empty:

                chart_df["request_number"] = range(
                    1,
                    len(chart_df) + 1,
                )

                st.line_chart(
                    chart_df.set_index("request_number")[
                        ["response_time_seconds"]
                    ],
                    color="#29dde7",
                    height=220,
                )

                st.caption(
                    "Each point represents a recorded request. "
                    + (
                        "Live mode records real provider request latency."
                        if use_live_providers
                        else "Demo mode measures local simulated execution."
                    )
                )

            else:
                st.info("No valid timestamps are available.")

        else:
            st.info(
                "No requests recorded yet. Open Routing & Failover "
                "to send your first test request."
            )

        st.markdown(
            '</div>',
            unsafe_allow_html=True,
        )

    with right:

        st.markdown(
            '<div class="panel">',
            unsafe_allow_html=True,
        )

        panel_heading(
            "Model Health",
            "Configured routing providers",
        )

        if use_live_providers:

            st.markdown(
                """
                <div class="model-card">
                    <div class="healthy">● PRIMARY PROVIDER</div><br>
                    <div class="model-name">Google Gemini</div>
                    <div class="model-role">Primary request route</div>
                </div>

                <div class="model-card">
                    <div style="color:#29dde7;font-size:11px;font-weight:700">
                        ● BACKUP PROVIDER
                    </div><br>
                    <div class="model-name">OpenAI</div>
                    <div class="model-role">Used when Gemini fails</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.caption(
                "Provider health is inferred from request outcomes, "
                "not from continuous health probes."
            )

        else:

            st.markdown(
                """
                <div class="model-card">
                    <div class="healthy">● DEMO PRIMARY</div><br>
                    <div class="model-name">Model A</div>
                    <div class="model-role">Primary simulated route</div>
                </div>

                <div class="model-card">
                    <div style="color:#29dde7;font-size:11px;font-weight:700">
                        ● DEMO BACKUP
                    </div><br>
                    <div class="model-name">Model B</div>
                    <div class="model-role">Backup simulated route</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.caption(
                "These are demo roles, not live provider health checks."
            )

        st.markdown(
            '</div>',
            unsafe_allow_html=True,
        )

    bottom_left, bottom_right = st.columns([1.35, 1])

    with bottom_left:

        st.markdown(
            '<div class="panel">',
            unsafe_allow_html=True,
        )

        panel_heading(
            "Recent Activity",
            "Latest recorded routing events",
        )

        if not df.empty:

            recent = df.tail(5).iloc[::-1]

            for _, row in recent.iterrows():

                timestamp = row["timestamp"]

                time_text = (
                    timestamp.strftime("%H:%M:%S UTC")
                    if pd.notna(timestamp)
                    else "Unknown time"
                )

                event_title = (
                    f"{row['model']} handled request"
                    if row["status"] == "success"
                    else "Request failed"
                )

                event_description = (
                    "Fallback was used"
                    if row["fallback_used"]
                    else "Primary route attempted"
                )

                st.markdown(
                    f"""
                    <div class="incident">
                        <div class="incident-time">
                            {time_text}
                        </div>
                        <div class="incident-title">
                            {event_title}
                        </div>
                        <div class="incident-description">
                            {event_description}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        else:
            st.info("No activity recorded yet.")

        st.markdown(
            '</div>',
            unsafe_allow_html=True,
        )

    with bottom_right:

        st.markdown(
            '<div class="panel">',
            unsafe_allow_html=True,
        )

        panel_heading(
            "Migration Readiness",
            "Replacement-model workflow",
        )

        steps = [
            ("01", "Candidate discovery", "To implement"),
            ("02", "Quality evaluation", "To implement"),
            ("03", "Compatibility checks", "To implement"),
            ("04", "Controlled migration", "To implement"),
        ]

        for number, title, status in steps:

            st.markdown(
                f"""
                <div class="incident">
                    <span style="color:#29dde7;font-weight:800">
                        {number}
                    </span>
                    &nbsp;&nbsp;
                    <span style="color:#e8f0fa;font-weight:600">
                        {title}
                    </span>
                    <div class="incident-description">
                        {status}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown(
            '</div>',
            unsafe_allow_html=True,
        )


# ==========================================
# MODEL HEALTH PAGE
# ==========================================

elif page == "Model Health":

    st.title("Model Health Monitor")

    st.markdown(
        '<div class="subtitle">'
        'Review real request outcomes by provider or simulated model.'
        '</div>',
        unsafe_allow_html=True,
    )

    if df.empty:

        st.info(
            "No recorded requests yet. Use Routing & Failover "
            "to send a test request."
        )

    else:

        model_names = sorted(
            df["model"]
            .fillna("Unknown model")
            .astype(str)
            .unique()
        )

        for model_name in model_names:

            model_df = df[
                df["model"]
                .fillna("Unknown model")
                .astype(str)
                == model_name
            ]

            successes = int(
                (model_df["status"] == "success").sum()
            )

            failed = int(
                (model_df["status"] == "failed").sum()
            )

            fallbacks = int(
                model_df["fallback_used"].sum()
            )

            a, b, c, d = st.columns(4)

            a.metric("Model / Provider", model_name)
            b.metric("Successful Requests", successes)
            c.metric("Failed Requests", failed)
            d.metric("Fallback-marked Requests", fallbacks)

            st.divider()

    st.info(
        "This page summarizes recorded requests. It does not run "
        "continuous health probes. A provider is only known to have "
        "worked when a request succeeds."
    )


# ==========================================
# ROUTING AND FAILOVER PAGE
# ==========================================

elif page == "Routing & Failover":

    st.title("Routing & Failover")

    st.markdown(
        '<div class="subtitle">'
        'Send a real request through Gemini → OpenAI, '
        'or test simulated failover.'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="panel">',
        unsafe_allow_html=True,
    )

    panel_heading(
        "Send a Test Request",
        "Live mode uses your API keys; demo mode uses simulated models.",
    )

    prompt = st.text_area(
        "Your prompt",
        value="Explain artificial intelligence in simple words.",
        height=120,
    )

    if not use_live_providers:

        primary_fails = st.toggle(
            "Simulate a Model A failure",
            value=False,
            help="Turn this on to test the simulated backup route.",
        )

    else:

        primary_fails = False

        st.info(
            "Live routing: Gemini is tried first. "
            "OpenAI is attempted if Gemini fails."
        )

    if st.button(
        "▶  Run Model Request",
        use_container_width=True,
    ):

        if not prompt.strip():

            st.error("Please enter a prompt.")

        else:

            start = time.perf_counter()

            if use_live_providers:

                # RealModelRouter logs its own request.
                router = RealModelRouter()
                result = router.generate(prompt)

                elapsed = time.perf_counter() - start

            else:

                primary = DemoModel(
                    "Model A",
                    should_fail=primary_fails,
                )

                backup = DemoModel(
                    "Model B",
                    should_fail=False,
                )

                router = ModelRouter(
                    primary,
                    backup,
                )

                result = router.generate(prompt)

                elapsed = time.perf_counter() - start

                status = (
                    "success"
                    if result.get("model")
                    else "failed"
                )

                log_request(
                    model=result.get("model"),
                    response_time=elapsed,
                    status=status,
                    fallback_used=result["fallback_used"],
                    error=result.get("error"),
                )

            st.session_state["last_result"] = result
            st.session_state["last_elapsed"] = elapsed
            st.session_state["last_live_mode"] = use_live_providers

    if "last_result" in st.session_state:

        result = st.session_state["last_result"]
        elapsed = st.session_state["last_elapsed"]

        st.markdown("---")
        st.subheader("Request Result")

        if result.get("model"):

            st.success(
                f"Request handled by {result['model']}"
            )

            if result.get("fallback_used"):
                st.warning(
                    "The backup route was used for this request."
                )

            st.write(result["response"])

        else:

            st.error(
                result.get(
                    "response",
                    "The request failed.",
                )
            )

        if result.get("error"):

            with st.expander("Technical error details"):
                st.code(result["error"])

        a, b, c = st.columns(3)

        a.metric(
            "Processing Time",
            f"{elapsed * 1000:.2f} ms",
        )

        b.metric(
            "Model Used",
            result.get("model") or "None",
        )

        c.metric(
            "Fallback Used",
            "Yes" if result.get("fallback_used") else "No",
        )

    st.markdown(
        '</div>',
        unsafe_allow_html=True,
    )


# ==========================================
# PERFORMANCE PAGE
# ==========================================

elif page == "Performance":

    st.title("Performance Analytics")

    st.markdown(
        '<div class="subtitle">'
        'Explore request latency, usage, and routing outcomes.'
        '</div>',
        unsafe_allow_html=True,
    )

    if df.empty:

        st.info(
            "No data is available yet. Send requests from "
            "Routing & Failover."
        )

    else:

        c1, c2 = st.columns(2)

        with c1:

            st.markdown(
                '<div class="panel">',
                unsafe_allow_html=True,
            )

            panel_heading(
                "Latency by Model",
                "Average measured processing time",
            )

            latency = (
                df.dropna(
                    subset=["response_time_seconds"]
                )
                .groupby("model")["response_time_seconds"]
                .mean()
            )

            if not latency.empty:
                st.bar_chart(
                    latency,
                    color="#29dde7",
                )

            st.markdown(
                '</div>',
                unsafe_allow_html=True,
            )

        with c2:

            st.markdown(
                '<div class="panel">',
                unsafe_allow_html=True,
            )

            panel_heading(
                "Requests by Model",
                "Number of requests handled",
            )

            usage = df["model"].value_counts()

            st.bar_chart(
                usage,
                color="#8b8aff",
            )

            st.markdown(
                '</div>',
                unsafe_allow_html=True,
            )

        st.subheader("Request Outcomes")

        outcomes = df["status"].value_counts()

        st.bar_chart(
            outcomes,
            color="#44dca4",
        )

        st.caption(
            "Live mode measures provider request latency. "
            "Demo mode measures local simulated execution."
        )


# ==========================================
# MIGRATION CENTER
# ==========================================

elif page == "Migration Center":

    st.title("Migration Center")

    st.markdown(
        '<div class="subtitle">'
        'Review lifecycle records and prepare model replacements safely.'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="panel">',
        unsafe_allow_html=True,
    )

    st.subheader("Migration Workflow")

    st.write(
        "A reliable migration evaluates a candidate before switching "
        "traffic. This dashboard does not automatically migrate "
        "production workloads."
    )

    migration_steps = [
        "Identify a replacement candidate",
        "Check API and feature compatibility",
        "Evaluate response quality on a test dataset",
        "Compare latency, cost, and reliability",
        "Test the candidate before production rollout",
        "Approve migration and preserve rollback capability",
    ]

    for index, step in enumerate(
        migration_steps,
        start=1,
    ):
        st.markdown(f"**{index}.** {step}")

    st.markdown(
        '</div>',
        unsafe_allow_html=True,
    )

    st.subheader("Registered Model Lifecycle")

    try:

        registry = ModelLifecycleRegistry()
        lifecycle_rows = registry.get_all_models()

        if lifecycle_rows:

            lifecycle_df = pd.DataFrame(lifecycle_rows)

            status_counts = lifecycle_df["status"].value_counts()

            metric_columns = st.columns(
                max(1, min(4, len(status_counts)))
            )

            for col, (status_name, count) in zip(
                metric_columns,
                status_counts.items(),
            ):

                col.metric(
                    status_name.replace("_", " ").title(),
                    int(count),
                )

            st.dataframe(
                lifecycle_df,
                use_container_width=True,
                hide_index=True,
            )

            st.download_button(
                "⬇ Download Lifecycle Registry",
                data=lifecycle_df.to_csv(
                    index=False
                ).encode("utf-8"),
                file_name="model_lifecycle_registry.csv",
                mime="text/csv",
            )

            st.caption(
                "Registry entries are extracted records and may include "
                "non-retirement rows. Verify model names, dates, and "
                "official notices before acting on them."
            )

        else:

            st.info(
                "The lifecycle registry is empty. "
                "Run the deprecation monitor first."
            )

    except Exception as error:

        st.warning(
            f"Could not load the lifecycle registry: {error}"
        )

    st.info(
        "Automatic candidate evaluation, traffic migration, and rollback "
        "are not implemented yet. The current migration center is a "
        "registry viewer and workflow guide."
    )


# ==========================================
# REQUEST LOGS PAGE
# ==========================================

elif page == "Request Logs":

    st.title("Request Logs")

    st.markdown(
        '<div class="subtitle">'
        'Inspect the records collected by AI Model Guardian.'
        '</div>',
        unsafe_allow_html=True,
    )

    if df.empty:

        st.info(
            "No request records exist yet. Run a test request first."
        )

    else:

        st.metric(
            "Total Logged Requests",
            len(df),
        )

        display_df = df.copy()

        display_df["timestamp"] = (
            display_df["timestamp"].astype(str)
        )

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
        )

        csv_data = display_df.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "⬇ Download Request Logs",
            data=csv_data,
            file_name="ai_model_guardian_logs.csv",
            mime="text/csv",
        )

    if st.button("Refresh Request Logs"):
        st.rerun()


# ==========================================
# FOOTER
# ==========================================

st.markdown("---")

st.caption(
    f"AI Model Guardian · Prototype · "
    f"Last page render: {datetime.now().strftime('%H:%M:%S')}"
)