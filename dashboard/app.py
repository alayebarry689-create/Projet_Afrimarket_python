"""
Dashboard interactif AfriMarket
Analyse stratégique de la performance e-commerce (Juillet - Décembre 2025)
"""

import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "df_clean.csv"
BRAND_DIR = ROOT / "assets" / "brand"

NAVY = "#152A4A"
GOLD = "#C9971C"

st.set_page_config(
    page_title="AfriMarket — Dashboard Stratégique",
    layout="wide",
    page_icon=str(BRAND_DIR / "favicon.png"),
)

# --- Habillage graphique (identité de marque Navy/Or) ---
px.defaults.color_discrete_sequence = [NAVY, GOLD, "#1565C0", "#2E7D32", "#C62828", "#6A4C93"]

st.markdown(
    f"""
    <style>
    div[data-testid="stMetric"] {{
        background-color: #F4F1EA;
        border: 1px solid #E8E2D4;
        border-left: 4px solid {GOLD};
        border-radius: 6px;
        padding: 10px 14px;
    }}
    div[data-testid="stMetricLabel"] {{ color: {NAVY}; }}
    h1, h2, h3 {{ color: {NAVY}; }}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH, parse_dates=["date_commande"])
    return df


df = load_data()

# ----------------------------------------------------------------------
# SIDEBAR — FILTRES
# ----------------------------------------------------------------------
st.sidebar.image(str(BRAND_DIR / "logo_full.png"), use_container_width=True)
st.sidebar.markdown("---")
st.sidebar.title("🔎 Filtres")

date_min, date_max = df["date_commande"].min(), df["date_commande"].max()
date_range = st.sidebar.date_input(
    "Période", value=(date_min, date_max), min_value=date_min, max_value=date_max
)

villes = st.sidebar.multiselect(
    "Ville", sorted(df["ville"].unique()), default=sorted(df["ville"].unique())
)
categories = st.sidebar.multiselect(
    "Catégorie", sorted(df["categorie"].unique()), default=sorted(df["categorie"].unique())
)
canaux = st.sidebar.multiselect(
    "Canal marketing", sorted(df["canal_marketing"].unique()), default=sorted(df["canal_marketing"].unique())
)
statuts = st.sidebar.multiselect(
    "Statut de commande", sorted(df["statut_commande"].unique()), default=sorted(df["statut_commande"].unique())
)

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = date_min, date_max

mask = (
    (df["date_commande"] >= pd.Timestamp(start_date))
    & (df["date_commande"] <= pd.Timestamp(end_date))
    & (df["ville"].isin(villes))
    & (df["categorie"].isin(categories))
    & (df["canal_marketing"].isin(canaux))
    & (df["statut_commande"].isin(statuts))
)
dff = df.loc[mask].copy()

st.sidebar.markdown("---")
st.sidebar.caption(f"{len(dff):,} commandes sélectionnées sur {len(df):,} au total")

# ----------------------------------------------------------------------
# HEADER
# ----------------------------------------------------------------------
col_logo, col_title = st.columns([1, 5])
with col_logo:
    st.image(str(BRAND_DIR / "logo_icon.png"), width=90)
with col_title:
    st.markdown(f"<h1 style='margin-bottom:0;color:{NAVY}'>Dashboard Stratégique</h1>", unsafe_allow_html=True)
    st.caption("E-commerce panafricain · Analyse Juillet – Décembre 2025")

if dff.empty:
    st.warning("Aucune donnée ne correspond aux filtres sélectionnés.")
    st.stop()

# ----------------------------------------------------------------------
# KPIs
# ----------------------------------------------------------------------
ca_total = dff["chiffre_affaires"].sum()
profit_total = dff["profit_net"].sum()
panier_moyen = dff.loc[dff["statut_commande"] != "Annulée", "chiffre_affaires"].mean()
taux_annulation = (dff["statut_commande"] == "Annulée").mean()
taux_retour = (dff["statut_commande"] == "Retournée").mean()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Chiffre d'affaires", f"{ca_total:,.0f} €")
c2.metric("Profit net estimé", f"{profit_total:,.0f} €")
c3.metric("Panier moyen", f"{panier_moyen:,.2f} €")
c4.metric("Taux d'annulation", f"{taux_annulation:.1%}")
c5.metric("Taux de retour", f"{taux_retour:.1%}")

st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(
    ["📦 Catégories", "🌍 Géographie", "📣 Marketing", "👥 Clients"]
)

# ----------------------------------------------------------------------
# TAB 1 — CATEGORIES
# ----------------------------------------------------------------------
with tab1:
    st.subheader("Performance par catégorie")

    cat_stats = (
        dff.groupby("categorie")
        .agg(
            CA=("chiffre_affaires", "sum"),
            Marge_brute=("marge_brute", "sum"),
            Profit_net=("profit_net", "sum"),
            Taux_retour=("indicateur_retour", "mean"),
            Nb_commandes=("id_commande", "count"),
        )
        .sort_values("CA", ascending=False)
        .reset_index()
    )
    cat_stats["Taux_retour_pct"] = (cat_stats["Taux_retour"] * 100).round(1)

    colA, colB = st.columns(2)
    with colA:
        fig = px.bar(cat_stats, x="categorie", y="CA", color="categorie",
                     title="Chiffre d'affaires par catégorie", text_auto=".2s")
        st.plotly_chart(fig, use_container_width=True)
    with colB:
        fig = px.bar(cat_stats, x="categorie", y="Taux_retour_pct", color="categorie",
                     title="Taux de retour par catégorie (%)", text="Taux_retour_pct")
        st.plotly_chart(fig, use_container_width=True)

    evo_cat = dff.groupby(["mois", "categorie"])["chiffre_affaires"].sum().reset_index()
    fig = px.line(evo_cat, x="mois", y="chiffre_affaires", color="categorie", markers=True,
                  title="Évolution mensuelle du CA par catégorie")
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        cat_stats[["categorie", "CA", "Marge_brute", "Profit_net", "Taux_retour_pct", "Nb_commandes"]]
        .rename(columns={"Taux_retour_pct": "Taux_retour (%)"}),
        use_container_width=True,
    )

# ----------------------------------------------------------------------
# TAB 2 — GEOGRAPHIE
# ----------------------------------------------------------------------
with tab2:
    st.subheader("Performance géographique")

    ville_stats = (
        dff.groupby("ville")
        .agg(
            CA=("chiffre_affaires", "sum"),
            Profit=("profit_net", "sum"),
            Taux_annulation=("statut_commande", lambda s: (s == "Annulée").mean()),
            Nb_commandes=("id_commande", "count"),
        )
        .sort_values("CA", ascending=False)
        .reset_index()
    )
    ville_stats["Taux_annulation_pct"] = (ville_stats["Taux_annulation"] * 100).round(1)

    colA, colB = st.columns(2)
    with colA:
        fig = px.bar(ville_stats, x="ville", y="CA", color="ville",
                     title="Chiffre d'affaires par ville", text_auto=".2s")
        st.plotly_chart(fig, use_container_width=True)
    with colB:
        fig = px.bar(ville_stats, x="ville", y="Taux_annulation_pct", color="ville",
                     title="Taux d'annulation par ville (%)", text="Taux_annulation_pct")
        st.plotly_chart(fig, use_container_width=True)

    croissance = dff.groupby(["mois", "ville"])["chiffre_affaires"].sum().reset_index()
    pivot = croissance.pivot(index="ville", columns="mois", values="chiffre_affaires").fillna(0)
    pivot = pivot.loc[ville_stats["ville"]]
    fig = px.imshow(pivot, aspect="auto", color_continuous_scale="YlGnBu",
                     title="Heatmap CA mensuel par ville", labels=dict(color="CA (€)"))
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        ville_stats[["ville", "CA", "Profit", "Taux_annulation_pct", "Nb_commandes"]]
        .rename(columns={"Taux_annulation_pct": "Taux_annulation (%)"}),
        use_container_width=True,
    )

# ----------------------------------------------------------------------
# TAB 3 — MARKETING
# ----------------------------------------------------------------------
with tab3:
    st.subheader("Performance marketing")

    mkt_stats = dff.groupby("canal_marketing").agg(
        CA=("chiffre_affaires", "sum"),
        Cout_marketing=("cout_marketing", "sum"),
        Nb_commandes=("id_commande", "count"),
        Nb_clients=("id_client", "nunique"),
    )
    mkt_stats["ROI"] = (mkt_stats["CA"] - mkt_stats["Cout_marketing"]) / mkt_stats["Cout_marketing"]

    retention = dff.groupby(["canal_marketing", "id_client"])["id_commande"].count().reset_index()
    retention["recurrent"] = retention["id_commande"] > 1
    mkt_stats["Taux_retention"] = retention.groupby("canal_marketing")["recurrent"].mean()
    mkt_stats = mkt_stats.sort_values("ROI", ascending=False).reset_index()
    mkt_stats["Taux_retention_pct"] = (mkt_stats["Taux_retention"] * 100).round(1)
    mkt_stats["ROI_round"] = mkt_stats["ROI"].round(1)

    colA, colB = st.columns(2)
    with colA:
        fig = px.bar(mkt_stats, x="canal_marketing", y="ROI_round", color="canal_marketing",
                     title="ROI par canal — ROI = (CA - Coût) / Coût", text="ROI_round")
        st.plotly_chart(fig, use_container_width=True)
    with colB:
        fig = px.bar(mkt_stats, x="canal_marketing", y=["CA", "Cout_marketing"],
                     barmode="group", title="CA vs Coût marketing par canal")
        st.plotly_chart(fig, use_container_width=True)

    fig = px.bar(mkt_stats, x="canal_marketing", y="Taux_retention_pct", color="canal_marketing",
                 title="Taux de rétention par canal (%)", text="Taux_retention_pct")
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        mkt_stats[["canal_marketing", "CA", "Cout_marketing", "ROI_round", "Taux_retention_pct", "Nb_commandes"]]
        .rename(columns={"ROI_round": "ROI", "Taux_retention_pct": "Taux_retention (%)"}),
        use_container_width=True,
    )

# ----------------------------------------------------------------------
# TAB 4 — CLIENTS
# ----------------------------------------------------------------------
with tab4:
    st.subheader("Analyse clients")

    nb_clients = dff["id_client"].nunique()
    commandes_par_client = dff.groupby("id_client")["id_commande"].count()
    pct_recurrents = (commandes_par_client > 1).mean()

    c1, c2 = st.columns(2)
    c1.metric("Nombre total de clients", f"{nb_clients:,}")
    c2.metric("% clients récurrents", f"{pct_recurrents:.1%}")

    ca_par_client = dff.groupby("id_client")["chiffre_affaires"].sum().sort_values(ascending=False)
    cum_pct = ca_par_client.cumsum() / ca_par_client.sum()
    n_pareto = (cum_pct <= 0.8).sum() + 1

    st.info(f"**Pareto 80/20** : {n_pareto} clients ({n_pareto/nb_clients:.1%} de la base) génèrent 80% du chiffre d'affaires.")

    colA, colB = st.columns([2, 1])
    with colA:
        pareto_df = pd.DataFrame({
            "rang": range(1, len(cum_pct) + 1),
            "cumul_pct": cum_pct.values * 100
        })
        fig = px.line(pareto_df, x="rang", y="cumul_pct", title="Courbe de Pareto — Concentration du CA")
        fig.add_hline(y=80, line_dash="dash", line_color="red")
        fig.add_vline(x=n_pareto, line_dash="dash", line_color="green")
        st.plotly_chart(fig, use_container_width=True)
    with colB:
        top10 = ca_par_client.head(10).reset_index()
        top10.columns = ["id_client", "CA total (€)"]
        st.markdown("**Top 10 clients**")
        st.dataframe(top10, use_container_width=True, hide_index=True)

    clients_df = dff.groupby("id_client").agg(
        CA=("chiffre_affaires", "sum"), Nb_commandes=("id_commande", "count")
    ).reset_index()
    med_ca, med_freq = clients_df["CA"].median(), clients_df["Nb_commandes"].median()

    def segmenter(row):
        if row["CA"] >= med_ca and row["Nb_commandes"] >= med_freq:
            return "Champions"
        elif row["CA"] >= med_ca:
            return "Gros acheteurs occasionnels"
        elif row["Nb_commandes"] >= med_freq:
            return "Fidèles à faible panier"
        return "À risque / occasionnels"

    clients_df["segment"] = clients_df.apply(segmenter, axis=1)
    seg_counts = clients_df["segment"].value_counts().reset_index()
    seg_counts.columns = ["segment", "count"]

    fig = px.pie(seg_counts, names="segment", values="count", hole=0.4,
                 title="Segmentation clients (fréquence x valeur)")
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.caption("Dashboard généré à partir de df_clean — Projet Python AfriMarket · Data Analyst")
