-- =============================================================================
-- SEED DATA — DEMO ONLY. All rows are FICTIONAL placeholders.
-- Org names prefixed [SAMPLE], phones are 555-xxxx, confidence='unverified'.
-- Purpose: drive the front-end demo so the ZIP-search UX can be reviewed
-- BEFORE any real (safe-route, verified) collection. NO real provider data,
-- NO member data, NO PHI/PII. Delete before loading production data.
-- =============================================================================

PRAGMA foreign_keys = ON;

-- --- provenance source (one demo source) ------------------------------------
INSERT INTO source (id, source_name, source_type, publisher, source_url, license,
    attribution_required, redistribution_ok, access_route, refresh_mode,
    date_checked, confidence, notes) VALUES
('src-sample', 'DEMO SAMPLE DATA (not a real source)', 'other', 'internal',
 'https://example.invalid/sample', 'CC0', 0, 1, 'open', 'snapshot',
 '2026-06-24', 'unverified', 'Fictional seed data for UI demo only.');

-- --- geography: 3 counties across 2 zones ------------------------------------
INSERT INTO county (fips, county_name, state, is_independent_city, population_2020) VALUES
('29095', 'Jackson', 'MO', 0, 717204),
('20091', 'Johnson', 'KS', 0, 609863),
('29077', 'Greene',  'MO', 0, 298915);

INSERT INTO zone (zone_id, zone_name, line_crossing, approx_population, major_metros) VALUES
(1, 'Kansas City Metro (Bi-State Core)', 1, 1860000, '["Kansas City MO","Overland Park","Olathe"]'),
(4, 'Southwest + South-Central Missouri (Ozarks + Bootheel)', 0, 1450000, '["Springfield","Joplin"]');

INSERT INTO county_zone (fips, zone_id) VALUES
('29095', 1), ('20091', 1), ('29077', 4);

INSERT INTO zip_county (zip, fips, res_ratio, is_primary, crosswalk_vintage, source_id) VALUES
('64111', '29095', 1.0, 1, '2026Q1-DEMO', 'src-sample'),
('66061', '20091', 1.0, 1, '2026Q1-DEMO', 'src-sample'),
('65806', '29077', 1.0, 1, '2026Q1-DEMO', 'src-sample');

INSERT INTO city_county (id, city_name, state, fips) VALUES
('cc1','Kansas City','MO','29095'),
('cc2','Olathe','KS','20091'),
('cc3','Springfield','MO','29077');

-- =============================================================================
-- Helper convention for seed rows:
--   org   o-<n>      location l-<n>   address ad-<n>
--   service sv-<n>   service_at_location sal-<n>   phone p-<n>
-- Each address carries fips + zone_id so v_resource_by_zip resolves.
-- =============================================================================

-- ===== ZONE 1 / Jackson MO (ZIP 64111) ======================================
INSERT INTO organization (id,name,description,website,source_id,source_url,date_checked,confidence) VALUES
('o-1','[SAMPLE] Eastside Community Food Pantry','Fictional demo pantry.','https://example.invalid/eastside','src-sample','https://example.invalid/eastside','2026-06-24','unverified'),
('o-2','[SAMPLE] KC Utility Relief Fund','Fictional demo utility-assistance org.','https://example.invalid/kcutil','src-sample','https://example.invalid/kcutil','2026-06-24','unverified'),
('o-3','[SAMPLE] Paws Pet Food Bank','Fictional demo pet-food bank.','https://example.invalid/paws','src-sample','https://example.invalid/paws','2026-06-24','unverified');

INSERT INTO location (id,organization_id,name,location_type,source_id,source_url,date_checked,confidence) VALUES
('l-1','o-1','Eastside Pantry Main','physical','src-sample','https://example.invalid/eastside','2026-06-24','unverified'),
('l-2','o-2','KC Utility Relief Office','physical','src-sample','https://example.invalid/kcutil','2026-06-24','unverified'),
('l-3','o-3','Paws Distribution Site','physical','src-sample','https://example.invalid/paws','2026-06-24','unverified');

INSERT INTO address (id,location_id,address_1,city,state_province,postal_code,fips,zone_id) VALUES
('ad-1','l-1','1200 E 12th St','Kansas City','MO','64111','29095',1),
('ad-2','l-2','450 Grand Blvd','Kansas City','MO','64111','29095',1),
('ad-3','l-3','88 Troost Ave','Kansas City','MO','64111','29095',1);

INSERT INTO service (id,organization_id,name,description,resource_bucket,application_process,fees,source_id,source_url,date_checked,confidence) VALUES
('sv-1','o-1','Emergency Food Box','Three-day grocery box, walk-in.','food','Walk in with ID. No appointment.','Free','src-sample','https://example.invalid/eastside','2026-06-24','unverified'),
('sv-2','o-2','Utility Shut-off Prevention','One-time assistance with overdue electric/gas bills.','utility','Call to schedule intake.','Free','src-sample','https://example.invalid/kcutil','2026-06-24','unverified'),
('sv-3','o-3','Pet Food Pantry','Monthly dog/cat food for low-income seniors.','pet_food','Walk in, monthly limit.','Free','src-sample','https://example.invalid/paws','2026-06-24','unverified');

INSERT INTO service_at_location (id,service_id,location_id) VALUES
('sal-1','sv-1','l-1'),('sal-2','sv-2','l-2'),('sal-3','sv-3','l-3');

INSERT INTO phone (id,organization_id,number,type) VALUES
('p-1','o-1','(816) 555-0142','voice'),
('p-2','o-2','(816) 555-0177','hotline'),
('p-3','o-3','(816) 555-0199','voice');

INSERT INTO schedule (id,service_id,description,byday) VALUES
('sch-1','sv-1','Mon-Fri 9am-1pm','MO,TU,WE,TH,FR'),
('sch-2','sv-2','Mon-Thu 10am-4pm','MO,TU,WE,TH'),
('sch-3','sv-3','Sat 9am-12pm','SA');

INSERT INTO eligibility (id,service_id,description,min_age) VALUES
('el-1','sv-1','Open to all; income at or below 185% FPL.',NULL),
('el-2','sv-2','Jackson County residents, past-due utility notice.',NULL),
('el-3','sv-3','Seniors 60+, household pet.',60);

-- ===== ZONE 1 / Johnson KS (ZIP 66061) ======================================
INSERT INTO organization (id,name,description,website,source_id,source_url,date_checked,confidence) VALUES
('o-4','[SAMPLE] Olathe Neighbors Food Bank','Fictional demo food bank.','https://example.invalid/olathe','src-sample','https://example.invalid/olathe','2026-06-24','unverified'),
('o-5','[SAMPLE] Johnson County Rent Help','Fictional demo rent-assistance org.','https://example.invalid/jorent','src-sample','https://example.invalid/jorent','2026-06-24','unverified'),
('o-6','[SAMPLE] RxBridge Prescription Aid','Fictional demo prescription-assistance org.','https://example.invalid/rxbridge','src-sample','https://example.invalid/rxbridge','2026-06-24','unverified');

INSERT INTO location (id,organization_id,name,location_type,source_id,source_url,date_checked,confidence) VALUES
('l-4','o-4','Olathe Neighbors Main','physical','src-sample','https://example.invalid/olathe','2026-06-24','unverified'),
('l-5','o-5','Rent Help Intake Center','physical','src-sample','https://example.invalid/jorent','2026-06-24','unverified'),
('l-6','o-6','RxBridge Clinic','physical','src-sample','https://example.invalid/rxbridge','2026-06-24','unverified');

INSERT INTO address (id,location_id,address_1,city,state_province,postal_code,fips,zone_id) VALUES
('ad-4','l-4','321 N Cherry St','Olathe','KS','66061','20091',1),
('ad-5','l-5','910 E Santa Fe St','Olathe','KS','66061','20091',1),
('ad-6','l-6','77 S Kansas Ave','Olathe','KS','66061','20091',1);

INSERT INTO service (id,organization_id,name,description,resource_bucket,application_process,fees,source_id,source_url,date_checked,confidence) VALUES
('sv-4','o-4','Senior Grocery Program','Weekly grocery pickup for seniors.','food','Register once by phone.','Free','src-sample','https://example.invalid/olathe','2026-06-24','unverified'),
('sv-5','o-5','Emergency Rent Assistance','Up to one month past-due rent.','rent','Online application + documents.','Free','src-sample','https://example.invalid/jorent','2026-06-24','unverified'),
('sv-6','o-6','Medication Copay Assistance','Helps cover prescription copays.','prescription','Call intake line.','Free','src-sample','https://example.invalid/rxbridge','2026-06-24','unverified');

INSERT INTO service_at_location (id,service_id,location_id) VALUES
('sal-4','sv-4','l-4'),('sal-5','sv-5','l-5'),('sal-6','sv-6','l-6');

INSERT INTO phone (id,organization_id,number,type) VALUES
('p-4','o-4','(913) 555-0120','voice'),
('p-5','o-5','(913) 555-0166','voice'),
('p-6','o-6','(913) 555-0188','hotline');

INSERT INTO schedule (id,service_id,description,byday) VALUES
('sch-4','sv-4','Wed 10am-2pm','WE'),
('sch-5','sv-5','Mon-Fri 8am-5pm','MO,TU,WE,TH,FR'),
('sch-6','sv-6','Tue,Thu 9am-3pm','TU,TH');

INSERT INTO eligibility (id,service_id,description,min_age) VALUES
('el-4','sv-4','Seniors 60+, Johnson County.',60),
('el-5','sv-5','Income at or below 50% AMI.',NULL),
('el-6','sv-6','Uninsured/underinsured residents.',NULL);

-- ===== ZONE 4 / Greene MO (ZIP 65806) =======================================
INSERT INTO organization (id,name,description,website,source_id,source_url,date_checked,confidence) VALUES
('o-7','[SAMPLE] Ozarks Food Harvest Partner','Fictional demo food org.','https://example.invalid/ozarks','src-sample','https://example.invalid/ozarks','2026-06-24','unverified'),
('o-8','[SAMPLE] Springfield Gas & Transport Aid','Fictional demo transportation-assistance org.','https://example.invalid/sgtransport','src-sample','https://example.invalid/sgtransport','2026-06-24','unverified');

INSERT INTO location (id,organization_id,name,location_type,source_id,source_url,date_checked,confidence) VALUES
('l-7','o-7','Ozarks Partner Pantry','physical','src-sample','https://example.invalid/ozarks','2026-06-24','unverified'),
('l-8','o-8','Transport Aid Office','physical','src-sample','https://example.invalid/sgtransport','2026-06-24','unverified');

INSERT INTO address (id,location_id,address_1,city,state_province,postal_code,fips,zone_id) VALUES
('ad-7','l-7','215 S Campbell Ave','Springfield','MO','65806','29077',4),
('ad-8','l-8','530 W College St','Springfield','MO','65806','29077',4);

INSERT INTO service (id,organization_id,name,description,resource_bucket,application_process,fees,source_id,source_url,date_checked,confidence) VALUES
('sv-7','o-7','Mobile Food Distribution','Drive-through grocery distribution.','food','Just show up; first-come.','Free','src-sample','https://example.invalid/ozarks','2026-06-24','unverified'),
('sv-8','o-8','Gas Card Assistance','Fuel cards for medical/work trips.','gas_transport','Call to request voucher.','Free','src-sample','https://example.invalid/sgtransport','2026-06-24','unverified');

INSERT INTO service_at_location (id,service_id,location_id) VALUES
('sal-7','sv-7','l-7'),('sal-8','sv-8','l-8');

INSERT INTO phone (id,organization_id,number,type) VALUES
('p-7','o-7','(417) 555-0133','voice'),
('p-8','o-8','(417) 555-0155','voice');

INSERT INTO schedule (id,service_id,description,byday) VALUES
('sch-7','sv-7','2nd Sat each month 9am','SA'),
('sch-8','sv-8','Mon-Fri 9am-12pm','MO,TU,WE,TH,FR');

INSERT INTO eligibility (id,service_id,description,min_age) VALUES
('el-7','sv-7','Open to all Greene County residents.',NULL),
('el-8','sv-8','Low-income, verified appointment/work need.',NULL);

-- =============================================================================
-- CARRIER BENEFITS LAYER — "what you are losing 1/1/2027" (FICTIONAL sample)
-- =============================================================================
INSERT INTO carrier_benefit (id,parent_company,carrier_brand,plan_name,plan_year,state,
    benefit_marketing_name,ssbci_flag,eligibility_conditions,allowance_amount,allowance_period,
    ends_effective_date,loss_summary,source_id,source_url,source_doc_type,date_checked,confidence) VALUES
('cb-1','[SAMPLE] Demo Health','[SAMPLE] Demo Advantage','Demo Advantage D-SNP',2026,'BOTH',
 'Healthy Options Allowance',1,'Chronically ill + dual-eligible',125.0,'monthly',
 '2027-01-01','You currently get $125/month for groceries and utility bills on your benefit card. This ends 1/1/2027 if you no longer qualify.',
 'src-sample','https://example.invalid/sample-sb','SB','2026-06-24','unverified'),
('cb-2','[SAMPLE] Demo Health','[SAMPLE] Demo Advantage','Demo Advantage D-SNP',2026,'MO',
 'Flex Pet & Transport Allowance',1,'Chronically ill',50.0,'monthly',
 '2027-01-01','You currently get $50/month toward pet food and gas/transportation. This ends 1/1/2027 if you no longer qualify.',
 'src-sample','https://example.invalid/sample-sb','SB','2026-06-24','unverified');

INSERT INTO carrier_benefit_county (benefit_id,fips) VALUES
('cb-1','29095'),('cb-1','20091'),('cb-1','29077'),
('cb-2','29095'),('cb-2','29077');

INSERT INTO benefit_category (id,benefit_id,category,resource_bucket,ssbci_gated) VALUES
('bc-1','cb-1','groceries','food',1),
('bc-2','cb-1','utilities','utility',1),
('bc-3','cb-2','pet_food','pet_food',1),
('bc-4','cb-2','transport_nonmedical','gas_transport',1);
