-- Comprehensive test data for treasuremap database
-- This file contains minimal test data for development and testing
-- All tables are represented with essential test data

-- Disable foreign key checks temporarily
SET session_replication_role = replica;

-- Clear existing data in dependency order
TRUNCATE TABLE public.pointing_event CASCADE;
TRUNCATE TABLE public.pointing CASCADE;
TRUNCATE TABLE public.footprint_ccd CASCADE;
TRUNCATE TABLE public.instrument CASCADE;
TRUNCATE TABLE public.gw_candidate CASCADE;
TRUNCATE TABLE public.icecube_notice_coinc_event CASCADE;
TRUNCATE TABLE public.icecube_notice CASCADE;
TRUNCATE TABLE public.gw_galaxy_score CASCADE;
TRUNCATE TABLE public.gw_galaxy_entry CASCADE;
TRUNCATE TABLE public.gw_galaxy_list CASCADE;
TRUNCATE TABLE public.gw_galaxy CASCADE;
TRUNCATE TABLE public.doi_author CASCADE;
TRUNCATE TABLE public.doi_author_group CASCADE;
TRUNCATE TABLE public.useractions CASCADE;
TRUNCATE TABLE public.usergroups CASCADE;
TRUNCATE TABLE public.groups CASCADE;
TRUNCATE TABLE public.users CASCADE;
TRUNCATE TABLE public.gw_alert CASCADE;
TRUNCATE TABLE public.glade_2p3 CASCADE;

-- ===========================================
-- IMPORTANT: TEST USER PASSWORDS ARE:
--   admin@test.com / admin123
--   test@test.com / test123
--   science@test.com / science123
-- ===========================================
-- Insert test users with working passwords
-- Password hashes generated with PBKDF2-SHA256
INSERT INTO public.users (id, username, firstname, lastname, password_hash, datecreated, email, verified, api_token)
VALUES 
    (1, 'admin', 'Admin', 'User', 'pbkdf2:sha256:100000$39a855b4095fbe6511426f8075bb12ea$30fb8a9603e081d7ea73f3886bda84f7b6b0a01e365e27e809976325d0b4e6b4', NOW(), 'admin@test.com', true, 'test_token_admin_001'),
    (2, 'testuser', 'Test', 'User', 'pbkdf2:sha256:100000$9023eca0628e0d47c2a3fc84299725f4$ee4c6d17f211a7c314bc26cb72c2417a2adc2841fc648f6dec6de545fc85615f', NOW(), 'test@test.com', true, 'test_token_user_002'),
    (3, 'scientist', 'Science', 'User', 'pbkdf2:sha256:100000$f3cd94c185e376ef3ccdb4336da4bba7$314583fd6b4f2d7da6d5f46d7dc07985ce455a1cbdebdec56fbf2de941c2cc51', NOW(), 'science@test.com', true, 'test_token_sci_003');

-- Insert test groups
INSERT INTO public.groups (id, name, datecreated)
VALUES
    (1, 'admin', NOW()),
    (2, 'researchers', NOW()),
    (3, 'observers', NOW());

-- Insert user-group relationships
INSERT INTO public.usergroups (id, userid, groupid, role)
VALUES
    (1, 1, 1, 'admin'),
    (2, 2, 2, 'member'),
    (3, 3, 2, 'member'),
    (4, 3, 3, 'lead');

-- Insert test GW alerts
INSERT INTO public.gw_alert (id, graceid, alternateid, role, time_of_signal, timesent, datecreated, alert_type, observing_run, far, distance, distance_error, prob_bns, prob_nsbh, prob_bbh, prob_terrestrial, area_50, area_90)
VALUES
    (1, 'S190425z', 'G298048', 'observation', '2019-04-25 08:18:05', '2019-04-25 08:18:26', NOW(), 'Preliminary', 'O3', 9.11e-6, 156.0, 41.0, 0.72, 0.23, 0.05, 0.00, 1131.0, 3818.0),
    (2, 'S190426c', 'G298146', 'observation', '2019-04-26 15:21:55', '2019-04-26 15:22:16', NOW(), 'Initial', 'O3', 1.23e-6, 377.0, 100.0, 0.00, 0.56, 0.44, 0.00, 1033.0, 3502.0),
    (3, 'MS230101a', NULL, 'test', '2023-01-01 00:00:00', '2023-01-01 00:01:00', NOW(), 'Preliminary', 'O4', 5.55e-8, 200.0, 50.0, 0.90, 0.05, 0.05, 0.00, 500.0, 1500.0),
    (4, 'GW190521', 'GW190521_074359', 'observation', '2020-05-21 07:43:59', '2020-05-21 07:43:35', NOW(), 'Initial', 'O3', 2.5e-7, 5300.0, 2600.0, 0.0, 0.0, 0.95, 0.04, 0.01, 0.0),
    (5, 'MS190425a', 'MS190425a-v1', 'test', '2019-04-25 15:00:00', '2019-04-25 15:00:00', NOW(), 'Test', 'O3', 1.0e-5, 100.0, 50.0, 0.5, 0.2, 0.1, 0.1, 0.7, 0.3);

-- Insert test instruments with proper enum values
-- instrument_type: photometric, spectroscopic
INSERT INTO public.instrument (id, instrument_name, nickname, instrument_type, datecreated, submitterid)
VALUES
    (1, 'Test Optical Telescope', 'TOT', 'photometric', NOW(), 1),
    (2, 'Test X-ray Observatory', 'TXO', 'spectroscopic', NOW(), 1),
    (3, 'Mock Radio Dish', 'MRD', 'photometric', NOW(), 2);

-- Insert test footprint CCDs
INSERT INTO public.footprint_ccd (id, instrumentid, footprint)
VALUES
    (1, 1, ST_GeomFromText('POLYGON((-1 -1, 1 -1, 1 1, -1 1, -1 -1))', 4326)),
    (2, 2, ST_GeomFromText('POLYGON((-0.5 -0.5, 0.5 -0.5, 0.5 0.5, -0.5 0.5, -0.5 -0.5))', 4326)),
    (3, 3, ST_GeomFromText('POLYGON((-2 -2, 2 -2, 2 2, -2 2, -2 -2))', 4326));

-- Insert test pointings with proper enum values
-- status: planned, completed, cancelled
-- depth_unit: ab_mag, vega_mag, flux_erg, flux_jy
-- band: U, B, V, R, I, J, H, K, u, g, r, i, z, etc.
INSERT INTO public.pointing (id, status, position, instrumentid, depth, depth_err, depth_unit, time, datecreated, dateupdated, submitterid, pos_angle, band, central_wave, bandwidth)
VALUES
    (1, 'completed', ST_GeomFromText('POINT(123.456 -12.345)', 4326), 1, 20.5, 0.1, 'ab_mag', '2019-04-25 09:00:00', NOW(), NULL, 1, 0.0, 'r', 6415.0, 1487.0),
    (2, 'planned', ST_GeomFromText('POINT(234.567 -23.456)', 4326), 2, 21.0, 0.2, 'ab_mag', '2019-04-25 10:00:00', NOW(), NULL, 2, 45.0, 'g', 4730.0, 1503.0),
    (3, 'completed', ST_GeomFromText('POINT(345.678 34.567)', 4326), 3, 19.8, 0.05, 'ab_mag', '2019-04-26 16:00:00', NOW(), NULL, 3, 90.0, 'i', 7836.0, 1468.0),
    (4, 'cancelled', ST_GeomFromText('POINT(456.789 45.678)', 4326), 1, 22.0, 0.1, 'ab_mag', '2019-04-26 18:00:00', NOW(), NOW(), 1, 0.0, 'r', 6415.0, 1487.0),
    (5, 'completed', ST_GeomFromText('POINT(150.0 -30.0)', 4326), 1, 20.5, 0.1, 'ab_mag', '2019-04-25 12:00:00', NOW(), NULL, 1, 45.0, 'V', 5338.0, 810.0),
    (6, 'completed', ST_GeomFromText('POINT(151.0 -30.0)', 4326), 1, 21.0, 0.1, 'ab_mag', '2019-04-25 12:30:00', NOW(), NULL, 1, 45.0, 'r', 6415.0, 1487.0),
    (7, 'completed', ST_GeomFromText('POINT(152.0 -30.0)', 4326), 1, 20.8, 0.1, 'ab_mag', '2019-04-25 13:00:00', NOW(), NULL, 1, 45.0, 'R', 6311.0, 1220.0),
    -- Planned pointings for GW190521
    (8, 'planned', ST_GeomFromText('POINT(134.0 35.0)', 4326), 1, 21.5, NULL, 'ab_mag', '2020-05-22 08:00:00', NOW(), NULL, 1, NULL, 'V', 5338.0, 810.0),
    (9, 'planned', ST_GeomFromText('POINT(135.0 35.0)', 4326), 1, 21.5, NULL, 'ab_mag', '2020-05-22 09:00:00', NOW(), NULL, 1, NULL, 'r', 6415.0, 1487.0),
    -- Cancelled pointing for MS190425a
    (10, 'cancelled', ST_GeomFromText('POINT(0.0 0.0)', 4326), 1, 20.0, NULL, 'ab_mag', '2019-04-25 16:00:00', NOW(), NOW(), 1, NULL, 'V', 5338.0, 810.0);

-- Insert pointing events (link pointings to GW events)
INSERT INTO public.pointing_event (id, pointingid, graceid)
VALUES
    (1, 1, 'S190425z'),
    (2, 2, 'S190425z'),
    (3, 3, 'S190426c'),
    (4, 4, 'S190426c'),
    (5, 5, 'S190425z'),
    (6, 6, 'S190425z'),
    (7, 7, 'S190425z'),
    (8, 8, 'GW190521'),
    (9, 9, 'GW190521'),
    (10, 10, 'MS190425a');

-- Insert test GLADE galaxies
INSERT INTO public.glade_2p3 (id, pgc_number, position, gwgc_name, _2mass_name, hyperleda_name, sdssdr12_name, distance, distance_error, redshift, bmag, bmag_err)
VALUES
    (1, 1234567, ST_GeomFromText('POINT(120.0 -10.0)', 4326), 'GWGC_TEST_1', '2MASS_J08000000-1000000', 'HyperLEDA_1', 'SDSS_J120000.00-100000.0', 45.2, 2.1, 0.033, 12.5, 0.1),
    (2, 2345678, ST_GeomFromText('POINT(230.0 -20.0)', 4326), 'GWGC_TEST_2', '2MASS_J15200000-2000000', 'HyperLEDA_2', 'SDSS_J230000.00-200000.0', 156.8, 5.5, 0.115, 14.2, 0.2),
    (3, 3456789, ST_GeomFromText('POINT(340.0 30.0)', 4326), 'GWGC_TEST_3', '2MASS_J22400000+3000000', 'HyperLEDA_3', 'SDSS_J340000.00+300000.0', 89.3, 3.2, 0.065, 13.1, 0.15);

-- Insert test GW galaxy mappings
INSERT INTO public.gw_galaxy (id, graceid, galaxy_catalog, galaxy_catalogid, reference)
VALUES
    (1, 'S190425z', 1, 1, 'GLADE v2.3'),
    (2, 'S190425z', 1, 2, 'GLADE v2.3');

-- Insert test galaxy scores with proper enum values
-- score_type: default
INSERT INTO public.gw_galaxy_score (id, gw_galaxyid, score_type, score)
VALUES
    (1, 1, 'default', 0.85),
    (2, 2, 'default', 0.72);

-- Insert DOI author groups
INSERT INTO public.doi_author_group (id, userid, name)
VALUES
    (1, 1, 'LIGO-Virgo Collaboration'),
    (2, 2, 'Test Observatory Team'),
    (3, 1, 'Test Observatory Group');

-- Insert DOI authors
INSERT INTO public.doi_author (id, name, affiliation, orcid, gnd, pos_order, author_groupid)
VALUES
    (1, 'Admin User', 'Test University', '0000-0000-0000-0001', NULL, 1, 1),
    (2, 'Science User', 'Test Observatory', '0000-0000-0000-0002', NULL, 2, 1),
    (3, 'Test User', 'Test Institute', NULL, NULL, 1, 2);

-- Insert test galaxy lists
INSERT INTO public.gw_galaxy_list (id, graceid, groupname, submitterid, reference, alertid, doi_url, doi_id)
VALUES
    (1, 'S190425z', 'Test Group', 2, 'arXiv:2019.12345', '1', NULL, NULL),
    (2, 'S190426c', 'Science Team', 3, 'ApJ 2020 000 000', '2', NULL, NULL);

-- Insert test galaxy entries
INSERT INTO public.gw_galaxy_entry (id, listid, name, score, position, rank, info)
VALUES
    (1, 1, 'NGC1234', 0.95, ST_GeomFromText('POINT(121.0 -11.0)', 4326), 1, '{"distance": 45.5, "type": "spiral"}'),
    (2, 1, 'NGC5678', 0.87, ST_GeomFromText('POINT(125.0 -15.0)', 4326), 2, '{"distance": 52.1, "type": "elliptical"}'),
    (3, 2, 'SDSS J1500', 0.73, ST_GeomFromText('POINT(231.0 -21.0)', 4326), 1, '{"distance": 158.3, "type": "dwarf"}');

-- Insert test IceCube notices
INSERT INTO public.icecube_notice (id, ref_id, graceid, alert_datetime, datecreated, observation_start, observation_stop, pval_generic, pval_bayesian, most_probable_direction_ra, most_probable_direction_dec, flux_sens_low, flux_sens_high, sens_energy_range_low, sens_energy_range_high)
VALUES
    (1, 'ICECUBE_ASTROTRACK_123456', 'S190425z', '2019-04-25 08:25:00', NOW(), '2019-04-25 08:00:00', '2019-04-25 09:00:00', 0.05, 0.03, 123.5, -12.3, 1.2e-10, 5.5e-9, 1e3, 1e6),
    (2, 'ICECUBE_ASTROTRACK_234567', 'S190426c', '2019-04-26 15:30:00', NOW(), '2019-04-26 15:00:00', '2019-04-26 16:00:00', 0.12, 0.08, 234.6, -23.4, 8.9e-11, 3.2e-9, 5e2, 5e5);

-- Insert test IceCube notice events
INSERT INTO public.icecube_notice_coinc_event (id, icecube_notice_id, datecreated, event_dt, ra, dec, containment_probability, event_pval_generic, event_pval_bayesian, ra_uncertainty, uncertainty_shape)
VALUES
    (1, 1, NOW(), 0.0, 123.5, -12.3, 0.5, 0.05, 0.03, 0.5, 'circular'),
    (2, 2, NOW(), 30.0, 234.6, -23.4, 0.7, 0.12, 0.08, 0.3, 'elliptical');

-- Insert test GW candidates with proper enum values
INSERT INTO public.gw_candidate (id, datecreated, submitterid, graceid, candidate_name, tns_name, tns_url, position, discovery_date, discovery_magnitude, magnitude_central_wave, magnitude_bandwidth, magnitude_unit, magnitude_bandpass, associated_galaxy, associated_galaxy_redshift, associated_galaxy_distance)
VALUES
    (1, NOW(), 2, 'S190425z', 'AT2019abc', '2019abc', 'https://www.wis-tns.org/object/2019abc', ST_GeomFromText('POINT(122.0 -11.5)', 4326), '2019-04-25 10:30:00', 18.5, 6415.0, 1487.0, 'ab_mag', 'r', 'NGC1234', 0.033, 45.5),
    (2, NOW(), 3, 'S190426c', 'AT2019def', '2019def', 'https://www.wis-tns.org/object/2019def', ST_GeomFromText('POINT(232.0 -21.5)', 4326), '2019-04-26 17:15:00', 19.2, 4730.0, 1503.0, 'ab_mag', 'g', NULL, NULL, NULL);

-- Insert test user actions
INSERT INTO public.useractions (id, userid, ipaddress, url, time, jsonvals, method)
VALUES
    (1, 1, '127.0.0.1', '/api/v1/pointings', NOW(), '{"filter": "graceid=S190425z"}', 'GET'),
    (2, 2, '192.168.1.100', '/api/v1/candidate', NOW(), '{"graceid": "S190425z"}', 'POST'),
    (3, 3, '10.0.0.50', '/alerts', NOW(), NULL, 'GET');

-- Re-enable foreign key checks
SET session_replication_role = DEFAULT;

-- Update sequences to avoid conflicts
SELECT setval('public.users_id_seq', 10);
SELECT setval('public.groups_id_seq', 10);
SELECT setval('public.usergroups_id_seq', 10);
SELECT setval('public.instrument_id_seq', 10);
SELECT setval('public.footprint_ccd_id_seq', 10);
SELECT setval('public.gw_alert_id_seq', 10);
SELECT setval('public.pointing_id_seq', 10);
SELECT setval('public.pointing_event_id_seq', 10);
SELECT setval('public.glade_2p3_id_seq', 10);
SELECT setval('public.gw_galaxy_id_seq', 10);
SELECT setval('public.gw_galaxy_score_id_seq', 10);
SELECT setval('public.doi_author_group_id_seq', 10);
SELECT setval('public.doi_author_id_seq', 10);
SELECT setval('public.gw_galaxy_list_id_seq', 10);
SELECT setval('public.gw_galaxy_entry_id_seq', 10);
SELECT setval('public.icecube_notice_id_seq', 10);
SELECT setval('public.icecube_notice_coinc_event_id_seq', 10);
SELECT setval('public.gw_candidate_id_seq', 10);
SELECT setval('public.useractions_id_seq', 10);

-- Analyze tables to update statistics
ANALYZE;
