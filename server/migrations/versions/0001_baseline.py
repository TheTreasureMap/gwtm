"""Baseline: the schema as it stood when Alembic was adopted.

Revision ID: 0001_baseline
Revises: 
Create Date: 2026-11-19 13:32:09.298591
"""

from alembic import op
import sqlalchemy as sa
import geoalchemy2
from geoalchemy2 import Geography

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "doi_author",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("affiliation", sa.String(), nullable=True),
        sa.Column("orcid", sa.String(), nullable=True),
        sa.Column("gnd", sa.String(), nullable=True),
        sa.Column("pos_order", sa.Integer(), nullable=True),
        sa.Column("author_groupid", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="public",
    )
    op.create_table(
        "doi_author_group",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("userid", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="public",
    )
    op.create_table(
        "event_galaxy",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("graceid", sa.String(), nullable=True),
        sa.Column("galaxy_catalog", sa.Integer(), nullable=True),
        sa.Column("galaxy_catalogid", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="public",
    )
    op.create_geospatial_table(
        "footprint_ccd",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("instrumentid", sa.Integer(), nullable=True),
        sa.Column(
            "footprint",
            Geography(
                geometry_type="POLYGON",
                srid=4326,
                dimension=2,
                spatial_index=False,
                from_text="ST_GeogFromText",
                name="geography",
            ),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="public",
    )
    op.create_geospatial_index(
        "idx_footprint_ccd_footprint",
        "footprint_ccd",
        ["footprint"],
        unique=False,
        schema="public",
        postgresql_using="gist",
        postgresql_ops={},
    )
    op.create_geospatial_table(
        "glade_2p3",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("pgc_number", sa.Integer(), nullable=True),
        sa.Column("distance", sa.Float(), nullable=True),
        sa.Column("distance_error", sa.Float(), nullable=True),
        sa.Column("redshift", sa.Float(), nullable=True),
        sa.Column("bmag", sa.Float(), nullable=True),
        sa.Column("bmag_err", sa.Float(), nullable=True),
        sa.Column(
            "position",
            Geography(
                geometry_type="POINT",
                srid=4326,
                dimension=2,
                spatial_index=False,
                from_text="ST_GeogFromText",
                name="geography",
            ),
            nullable=True,
        ),
        sa.Column("_2mass_name", sa.String(), nullable=True),
        sa.Column("gwgc_name", sa.String(), nullable=True),
        sa.Column("hyperleda_name", sa.String(), nullable=True),
        sa.Column("sdssdr12_name", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="public",
    )
    op.create_geospatial_index(
        "idx_glade_2p3_position",
        "glade_2p3",
        ["position"],
        unique=False,
        schema="public",
        postgresql_using="gist",
        postgresql_ops={},
    )
    op.create_table(
        "groups",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=25), nullable=True),
        sa.Column("datecreated", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="public",
    )
    op.create_table(
        "gw_alert",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("datecreated", sa.DateTime(), nullable=True),
        sa.Column("graceid", sa.String(length=50), nullable=False),
        sa.Column("alternateid", sa.String(length=50), nullable=True),
        sa.Column("role", sa.String(length=20), nullable=True),
        sa.Column("timesent", sa.DateTime(), nullable=True),
        sa.Column("time_of_signal", sa.DateTime(), nullable=True),
        sa.Column("packet_type", sa.Integer(), nullable=True),
        sa.Column("alert_type", sa.String(length=50), nullable=True),
        sa.Column("detectors", sa.String(length=100), nullable=True),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("far", sa.Float(), nullable=True),
        sa.Column("skymap_fits_url", sa.String(length=500), nullable=True),
        sa.Column("distance", sa.Float(), nullable=True),
        sa.Column("distance_error", sa.Float(), nullable=True),
        sa.Column("prob_bns", sa.Float(), nullable=True),
        sa.Column("prob_nsbh", sa.Float(), nullable=True),
        sa.Column("prob_gap", sa.Float(), nullable=True),
        sa.Column("prob_bbh", sa.Float(), nullable=True),
        sa.Column("prob_terrestrial", sa.Float(), nullable=True),
        sa.Column("prob_hasns", sa.Float(), nullable=True),
        sa.Column("prob_hasremenant", sa.Float(), nullable=True),
        sa.Column("group", sa.String(length=50), nullable=True),
        sa.Column("centralfreq", sa.Float(), nullable=True),
        sa.Column("duration", sa.Float(), nullable=True),
        sa.Column("avgra", sa.Float(), nullable=True),
        sa.Column("avgdec", sa.Float(), nullable=True),
        sa.Column("observing_run", sa.String(length=20), nullable=True),
        sa.Column("pipeline", sa.String(length=50), nullable=True),
        sa.Column("search", sa.String(length=50), nullable=True),
        sa.Column("area_50", sa.Float(), nullable=True),
        sa.Column("area_90", sa.Float(), nullable=True),
        sa.Column("gcn_notice_id", sa.Integer(), nullable=True),
        sa.Column("ivorn", sa.String(length=100), nullable=True),
        sa.Column("ext_coinc_observatory", sa.String(length=50), nullable=True),
        sa.Column("ext_coinc_search", sa.String(length=50), nullable=True),
        sa.Column("time_difference", sa.Float(), nullable=True),
        sa.Column("time_coincidence_far", sa.Float(), nullable=True),
        sa.Column("time_sky_position_coincidence_far", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="public",
    )
    op.create_index(
        op.f("ix_public_gw_alert_alternateid"),
        "gw_alert",
        ["alternateid"],
        unique=False,
        schema="public",
    )
    op.create_index(
        op.f("ix_public_gw_alert_avgdec"),
        "gw_alert",
        ["avgdec"],
        unique=False,
        schema="public",
    )
    op.create_index(
        op.f("ix_public_gw_alert_far"),
        "gw_alert",
        ["far"],
        unique=False,
        schema="public",
    )
    op.create_index(
        op.f("ix_public_gw_alert_graceid"),
        "gw_alert",
        ["graceid"],
        unique=False,
        schema="public",
    )
    op.create_index(
        op.f("ix_public_gw_alert_role"),
        "gw_alert",
        ["role"],
        unique=False,
        schema="public",
    )
    op.create_index(
        op.f("ix_public_gw_alert_time_of_signal"),
        "gw_alert",
        ["time_of_signal"],
        unique=False,
        schema="public",
    )
    op.create_geospatial_table(
        "gw_candidate",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("graceid", sa.String(length=50), nullable=False),
        sa.Column("submitterid", sa.Integer(), nullable=False),
        sa.Column("candidate_name", sa.String(length=100), nullable=False),
        sa.Column("datecreated", sa.DateTime(), nullable=True),
        sa.Column("tns_name", sa.String(length=100), nullable=True),
        sa.Column("tns_url", sa.String(length=500), nullable=True),
        sa.Column(
            "position",
            Geography(
                geometry_type="POINT",
                srid=4326,
                dimension=2,
                spatial_index=False,
                from_text="ST_GeogFromText",
                name="geography",
                nullable=False,
            ),
            nullable=False,
        ),
        sa.Column("discovery_date", sa.DateTime(), nullable=True),
        sa.Column("discovery_magnitude", sa.Float(), nullable=True),
        sa.Column("magnitude_central_wave", sa.Float(), nullable=True),
        sa.Column("magnitude_bandwidth", sa.Float(), nullable=True),
        sa.Column(
            "magnitude_unit",
            sa.Enum("ab_mag", "vega_mag", "flux_erg", "flux_jy", name="depthunit"),
            nullable=False,
        ),
        sa.Column("magnitude_bandpass", sa.String(length=50), nullable=True),
        sa.Column("associated_galaxy", sa.String(length=100), nullable=True),
        sa.Column("associated_galaxy_redshift", sa.Float(), nullable=True),
        sa.Column("associated_galaxy_distance", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="public",
    )
    op.create_geospatial_index(
        "idx_gw_candidate_position",
        "gw_candidate",
        ["position"],
        unique=False,
        schema="public",
        postgresql_using="gist",
        postgresql_ops={},
    )
    op.create_table(
        "gw_galaxy",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("graceid", sa.String(), nullable=True),
        sa.Column("galaxy_catalog", sa.Integer(), nullable=True),
        sa.Column("galaxy_catalogid", sa.Integer(), nullable=True),
        sa.Column("reference", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="public",
    )
    op.create_geospatial_table(
        "gw_galaxy_entry",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("listid", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column(
            "position",
            Geography(
                geometry_type="POINT",
                srid=4326,
                dimension=2,
                spatial_index=False,
                from_text="ST_GeogFromText",
                name="geography",
            ),
            nullable=True,
        ),
        sa.Column("rank", sa.Integer(), nullable=True),
        sa.Column("info", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="public",
    )
    op.create_geospatial_index(
        "idx_gw_galaxy_entry_position",
        "gw_galaxy_entry",
        ["position"],
        unique=False,
        schema="public",
        postgresql_using="gist",
        postgresql_ops={},
    )
    op.create_table(
        "gw_galaxy_list",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("graceid", sa.String(), nullable=True),
        sa.Column("groupname", sa.String(), nullable=True),
        sa.Column("submitterid", sa.Integer(), nullable=True),
        sa.Column("reference", sa.String(), nullable=True),
        sa.Column("alertid", sa.String(), nullable=True),
        sa.Column("doi_url", sa.String(length=100), nullable=True),
        sa.Column("doi_id", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="public",
    )
    op.create_table(
        "gw_galaxy_score",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("gw_galaxyid", sa.Integer(), nullable=True),
        sa.Column(
            "score_type", sa.Enum("default", name="gwgalaxyscoretype"), nullable=True
        ),
        sa.Column("score", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="public",
    )
    op.create_table(
        "icecube_notice",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ref_id", sa.String(), nullable=True),
        sa.Column("graceid", sa.String(), nullable=True),
        sa.Column("alert_datetime", sa.DateTime(), nullable=True),
        sa.Column("datecreated", sa.DateTime(), nullable=True),
        sa.Column("observation_start", sa.DateTime(), nullable=True),
        sa.Column("observation_stop", sa.DateTime(), nullable=True),
        sa.Column("pval_generic", sa.Float(), nullable=True),
        sa.Column("pval_bayesian", sa.Float(), nullable=True),
        sa.Column("most_probable_direction_ra", sa.Float(), nullable=True),
        sa.Column("most_probable_direction_dec", sa.Float(), nullable=True),
        sa.Column("flux_sens_low", sa.Float(), nullable=True),
        sa.Column("flux_sens_high", sa.Float(), nullable=True),
        sa.Column("sens_energy_range_low", sa.Float(), nullable=True),
        sa.Column("sens_energy_range_high", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="public",
    )
    op.create_table(
        "icecube_notice_coinc_event",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("icecube_notice_id", sa.Integer(), nullable=True),
        sa.Column("datecreated", sa.DateTime(), nullable=True),
        sa.Column("event_dt", sa.Float(), nullable=True),
        sa.Column("ra", sa.Float(), nullable=True),
        sa.Column("dec", sa.Float(), nullable=True),
        sa.Column("containment_probability", sa.Float(), nullable=True),
        sa.Column("event_pval_generic", sa.Float(), nullable=True),
        sa.Column("event_pval_bayesian", sa.Float(), nullable=True),
        sa.Column("ra_uncertainty", sa.Float(), nullable=True),
        sa.Column("uncertainty_shape", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="public",
    )
    op.create_table(
        "instrument",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("instrument_name", sa.String(length=64), nullable=True),
        sa.Column("nickname", sa.String(length=25), nullable=True),
        sa.Column(
            "instrument_type",
            sa.Enum("photometric", "spectroscopic", name="instrumenttype"),
            nullable=True,
        ),
        sa.Column("datecreated", sa.DateTime(), nullable=True),
        sa.Column("submitterid", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="public",
    )
    op.create_geospatial_table(
        "pointing",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("planned", "completed", "cancelled", name="pointing_status"),
            nullable=True,
        ),
        sa.Column(
            "position",
            Geography(
                geometry_type="POINT",
                srid=4326,
                dimension=2,
                spatial_index=False,
                from_text="ST_GeogFromText",
                name="geography",
            ),
            nullable=True,
        ),
        sa.Column("galaxy_catalog", sa.Integer(), nullable=True),
        sa.Column("galaxy_catalogid", sa.Integer(), nullable=True),
        sa.Column("instrumentid", sa.Integer(), nullable=True),
        sa.Column("depth", sa.Float(), nullable=True),
        sa.Column("depth_err", sa.Float(), nullable=True),
        sa.Column(
            "depth_unit",
            sa.Enum("ab_mag", "vega_mag", "flux_erg", "flux_jy", name="depth_unit"),
            nullable=True,
        ),
        sa.Column("time", sa.DateTime(), nullable=True),
        sa.Column("datecreated", sa.DateTime(), nullable=True),
        sa.Column("dateupdated", sa.DateTime(), nullable=True),
        sa.Column("submitterid", sa.Integer(), nullable=True),
        sa.Column("pos_angle", sa.Float(), nullable=True),
        sa.Column(
            "band",
            sa.Enum(
                "U",
                "B",
                "V",
                "R",
                "I",
                "J",
                "H",
                "K",
                "u",
                "g",
                "r",
                "i",
                "z",
                "UVW1",
                "UVW2",
                "UVM2",
                "XRT",
                "clear",
                "open",
                "UHF",
                "VHF",
                "L",
                "S",
                "C",
                "X",
                "other",
                "TESS",
                "BAT",
                "HESS",
                "WISEL",
                "q",
                name="bandpass",
            ),
            nullable=True,
        ),
        sa.Column("doi_url", sa.String(length=100), nullable=True),
        sa.Column("doi_id", sa.Integer(), nullable=True),
        sa.Column("central_wave", sa.Float(), nullable=True),
        sa.Column("bandwidth", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="public",
    )
    op.create_geospatial_index(
        "idx_pointing_position",
        "pointing",
        ["position"],
        unique=False,
        schema="public",
        postgresql_using="gist",
        postgresql_ops={},
    )
    op.create_table(
        "pointing_event",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("pointingid", sa.Integer(), nullable=True),
        sa.Column("graceid", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="public",
    )
    op.create_index(
        op.f("ix_public_pointing_event_graceid"),
        "pointing_event",
        ["graceid"],
        unique=False,
        schema="public",
    )
    op.create_index(
        op.f("ix_public_pointing_event_pointingid"),
        "pointing_event",
        ["pointingid"],
        unique=False,
        schema="public",
    )
    op.create_table(
        "useractions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("userid", sa.Integer(), nullable=True),
        sa.Column("ipaddress", sa.String(length=50), nullable=True),
        sa.Column("url", sa.String(), nullable=True),
        sa.Column("time", sa.DateTime(), nullable=True),
        sa.Column("jsonvals", sa.JSON(), nullable=True),
        sa.Column("method", sa.String(length=24), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="public",
    )
    op.create_table(
        "usergroups",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("userid", sa.Integer(), nullable=True),
        sa.Column("groupid", sa.Integer(), nullable=True),
        sa.Column("role", sa.String(length=25), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="public",
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=25), nullable=True),
        sa.Column("firstname", sa.String(length=25), nullable=True),
        sa.Column("lastname", sa.String(length=25), nullable=True),
        sa.Column("password_hash", sa.String(length=128), nullable=True),
        sa.Column("datecreated", sa.DateTime(), nullable=True),
        sa.Column("email", sa.String(length=100), nullable=True),
        sa.Column("verified", sa.Boolean(), nullable=True),
        sa.Column("api_token", sa.String(length=128), nullable=True),
        sa.Column("verification_key", sa.String(length=128), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="public",
    )
    op.create_index(
        op.f("ix_public_users_email"), "users", ["email"], unique=True, schema="public"
    )
    op.create_index(
        op.f("ix_public_users_username"),
        "users",
        ["username"],
        unique=True,
        schema="public",
    )


def downgrade():
    raise NotImplementedError(
        "The baseline is the oldest schema; there is nothing to downgrade to."
    )
