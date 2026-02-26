"""
Synthetic medical dataset for MedGraphRAG.
Covers diseases, symptoms, drugs, interactions, genes, and comorbidities.
Run this script to generate data/processed/synthetic_medical_data.json
"""

import json
import os


# DISEASES
DISEASES = [
    {
        "name": "Type 2 Diabetes Mellitus",
        "icd_code": "E11",
        "description": (
            "A chronic metabolic disorder characterized by high blood glucose "
            "levels due to insulin resistance and relative insulin deficiency."
        ),
        "category": "Endocrine",
    },
    {
        "name": "Hypertension",
        "icd_code": "I10",
        "description": (
            "A condition in which blood pressure in the arteries is persistently "
            "elevated, increasing the risk of heart disease and stroke."
        ),
        "category": "Cardiovascular",
    },
    {
        "name": "Coronary Artery Disease",
        "icd_code": "I25",
        "description": (
            "Narrowing or blockage of the coronary arteries, usually caused by "
            "atherosclerosis, reducing blood flow to the heart muscle."
        ),
        "category": "Cardiovascular",
    },
    {
        "name": "Chronic Kidney Disease",
        "icd_code": "N18",
        "description": (
            "Progressive loss of kidney function over months or years, "
            "classified in stages 1 through 5 based on GFR."
        ),
        "category": "Renal",
    },
    {
        "name": "Asthma",
        "icd_code": "J45",
        "description": (
            "A chronic respiratory disease characterized by airway inflammation, "
            "bronchospasm, and reversible airflow obstruction."
        ),
        "category": "Respiratory",
    },
    {
        "name": "Major Depressive Disorder",
        "icd_code": "F32",
        "description": (
            "A mood disorder causing persistent feelings of sadness, hopelessness, "
            "and loss of interest that interfere with daily functioning."
        ),
        "category": "Psychiatric",
    },
    {
        "name": "Hypothyroidism",
        "icd_code": "E03",
        "description": (
            "Underactivity of the thyroid gland resulting in insufficient "
            "production of thyroid hormones, slowing metabolic processes."
        ),
        "category": "Endocrine",
    },
    {
        "name": "Atrial Fibrillation",
        "icd_code": "I48",
        "description": (
            "An irregular and often rapid heart rate that can increase the risk "
            "of stroke, heart failure, and other cardiac complications."
        ),
        "category": "Cardiovascular",
    },
    {
        "name": "Chronic Obstructive Pulmonary Disease",
        "icd_code": "J44",
        "description": (
            "A chronic inflammatory lung disease that causes obstructed airflow "
            "from the lungs, including emphysema and chronic bronchitis."
        ),
        "category": "Respiratory",
    },
    {
        "name": "Osteoarthritis",
        "icd_code": "M15",
        "description": (
            "Degenerative joint disease involving breakdown of cartilage and "
            "underlying bone, causing pain, stiffness, and reduced mobility."
        ),
        "category": "Musculoskeletal",
    },
]


# SYMPTOMS  (name, description)
SYMPTOMS = [
    {"name": "Polyuria", "description": "Excessive urination, often more than 3 liters per day."},
    {"name": "Polydipsia", "description": "Excessive thirst due to dehydration or high blood glucose."},
    {"name": "Fatigue", "description": "Persistent tiredness not relieved by rest."},
    {"name": "Blurred Vision", "description": "Decreased sharpness of vision."},
    {"name": "Headache", "description": "Pain in the head or upper neck."},
    {"name": "Chest Pain", "description": "Discomfort or pain in the chest region."},
    {"name": "Shortness of Breath", "description": "Difficulty breathing or feeling breathless."},
    {"name": "Palpitations", "description": "Sensations of a rapid or irregular heartbeat."},
    {"name": "Edema", "description": "Swelling caused by excess fluid trapped in body tissues."},
    {"name": "Nausea", "description": "Unpleasant sensation that may precede vomiting."},
    {"name": "Weight Gain", "description": "Increase in body weight over time."},
    {"name": "Cold Intolerance", "description": "Unusual sensitivity to cold temperatures."},
    {"name": "Constipation", "description": "Infrequent or difficult bowel movements."},
    {"name": "Wheezing", "description": "High-pitched whistling sound during breathing."},
    {"name": "Cough", "description": "Sudden expulsion of air from the lungs."},
    {"name": "Sadness", "description": "Persistent low mood or feeling of hopelessness."},
    {"name": "Insomnia", "description": "Difficulty falling or staying asleep."},
    {"name": "Joint Pain", "description": "Discomfort or aching in one or more joints."},
    {"name": "Joint Stiffness", "description": "Reduced range of motion, especially in the morning."},
    {"name": "Irregular Heartbeat", "description": "Heart rhythm that is too fast, too slow, or uneven."},
    {"name": "Dizziness", "description": "Feeling of lightheadedness or unsteadiness."},
    {"name": "Proteinuria", "description": "Presence of excess protein in the urine."},
    {"name": "Decreased Appetite", "description": "Reduced desire to eat food."},
    {"name": "Sputum Production", "description": "Excess mucus produced and coughed up from the airways."},
]


# DRUGS  (name, drug_class, mechanism)
DRUGS = [
    {
        "name": "Metformin",
        "drug_class": "Biguanide",
        "mechanism": "Reduces hepatic glucose production and improves insulin sensitivity.",
    },
    {
        "name": "Lisinopril",
        "drug_class": "ACE Inhibitor",
        "mechanism": "Inhibits angiotensin-converting enzyme, reducing blood pressure and cardiac load.",
    },
    {
        "name": "Aspirin",
        "drug_class": "NSAID / Antiplatelet",
        "mechanism": "Irreversibly inhibits COX-1 and COX-2, reducing inflammation and platelet aggregation.",
    },
    {
        "name": "Atorvastatin",
        "drug_class": "Statin",
        "mechanism": "Inhibits HMG-CoA reductase, reducing LDL cholesterol synthesis.",
    },
    {
        "name": "Levothyroxine",
        "drug_class": "Thyroid Hormone",
        "mechanism": "Synthetic T4 that replaces or supplements natural thyroid hormone.",
    },
    {
        "name": "Sertraline",
        "drug_class": "SSRI",
        "mechanism": "Selectively inhibits serotonin reuptake, increasing synaptic serotonin levels.",
    },
    {
        "name": "Amlodipine",
        "drug_class": "Calcium Channel Blocker",
        "mechanism": "Blocks voltage-gated calcium channels in vascular smooth muscle, reducing blood pressure.",
    },
    {
        "name": "Warfarin",
        "drug_class": "Anticoagulant",
        "mechanism": "Inhibits vitamin K epoxide reductase, reducing synthesis of clotting factors.",
    },
    {
        "name": "Salbutamol",
        "drug_class": "Beta-2 Agonist",
        "mechanism": "Activates beta-2 adrenergic receptors, causing bronchodilation.",
    },
    {
        "name": "Furosemide",
        "drug_class": "Loop Diuretic",
        "mechanism": "Inhibits Na-K-2Cl cotransporter in the loop of Henle, promoting diuresis.",
    },
    {
        "name": "Ibuprofen",
        "drug_class": "NSAID",
        "mechanism": "Inhibits COX-1 and COX-2 enzymes, reducing prostaglandin synthesis.",
    },
    {
        "name": "Amiodarone",
        "drug_class": "Antiarrhythmic",
        "mechanism": "Blocks multiple ion channels, prolonging action potential and refractory period.",
    },
    {
        "name": "Tiotropium",
        "drug_class": "Anticholinergic",
        "mechanism": "Long-acting muscarinic antagonist that promotes bronchodilation.",
    },
    {
        "name": "Omeprazole",
        "drug_class": "Proton Pump Inhibitor",
        "mechanism": "Irreversibly inhibits H+/K+ ATPase in gastric parietal cells, reducing acid secretion.",
    },
    {
        "name": "Clopidogrel",
        "drug_class": "Antiplatelet",
        "mechanism": "Irreversibly inhibits P2Y12 ADP receptor on platelets, preventing aggregation.",
    },
]


# DISEASE → SYMPTOM  relationships
DISEASE_SYMPTOMS = [
    # Type 2 Diabetes
    ("Type 2 Diabetes Mellitus", "Polyuria"),
    ("Type 2 Diabetes Mellitus", "Polydipsia"),
    ("Type 2 Diabetes Mellitus", "Fatigue"),
    ("Type 2 Diabetes Mellitus", "Blurred Vision"),
    ("Type 2 Diabetes Mellitus", "Weight Gain"),
    # Hypertension
    ("Hypertension", "Headache"),
    ("Hypertension", "Dizziness"),
    ("Hypertension", "Blurred Vision"),
    ("Hypertension", "Chest Pain"),
    # Coronary Artery Disease
    ("Coronary Artery Disease", "Chest Pain"),
    ("Coronary Artery Disease", "Shortness of Breath"),
    ("Coronary Artery Disease", "Fatigue"),
    ("Coronary Artery Disease", "Palpitations"),
    # Chronic Kidney Disease
    ("Chronic Kidney Disease", "Edema"),
    ("Chronic Kidney Disease", "Fatigue"),
    ("Chronic Kidney Disease", "Nausea"),
    ("Chronic Kidney Disease", "Proteinuria"),
    # Asthma
    ("Asthma", "Wheezing"),
    ("Asthma", "Shortness of Breath"),
    ("Asthma", "Cough"),
    ("Asthma", "Chest Pain"),
    # Major Depressive Disorder
    ("Major Depressive Disorder", "Sadness"),
    ("Major Depressive Disorder", "Insomnia"),
    ("Major Depressive Disorder", "Fatigue"),
    ("Major Depressive Disorder", "Decreased Appetite"),
    # Hypothyroidism
    ("Hypothyroidism", "Fatigue"),
    ("Hypothyroidism", "Weight Gain"),
    ("Hypothyroidism", "Cold Intolerance"),
    ("Hypothyroidism", "Constipation"),
    # Atrial Fibrillation
    ("Atrial Fibrillation", "Palpitations"),
    ("Atrial Fibrillation", "Irregular Heartbeat"),
    ("Atrial Fibrillation", "Shortness of Breath"),
    ("Atrial Fibrillation", "Dizziness"),
    # COPD
    ("Chronic Obstructive Pulmonary Disease", "Shortness of Breath"),
    ("Chronic Obstructive Pulmonary Disease", "Cough"),
    ("Chronic Obstructive Pulmonary Disease", "Sputum Production"),
    ("Chronic Obstructive Pulmonary Disease", "Fatigue"),
    # Osteoarthritis
    ("Osteoarthritis", "Joint Pain"),
    ("Osteoarthritis", "Joint Stiffness"),
    ("Osteoarthritis", "Fatigue"),
]

# DRUG → DISEASE  (TREATS) with evidence level
DRUG_TREATS = [
    # Diabetes
    ("Metformin", "Type 2 Diabetes Mellitus", "Level A"),
    ("Atorvastatin", "Type 2 Diabetes Mellitus", "Level B"),
    # Hypertension
    ("Lisinopril", "Hypertension", "Level A"),
    ("Amlodipine", "Hypertension", "Level A"),
    ("Furosemide", "Hypertension", "Level B"),
    # Coronary Artery Disease
    ("Aspirin", "Coronary Artery Disease", "Level A"),
    ("Atorvastatin", "Coronary Artery Disease", "Level A"),
    ("Clopidogrel", "Coronary Artery Disease", "Level A"),
    ("Lisinopril", "Coronary Artery Disease", "Level B"),
    # Chronic Kidney Disease
    ("Lisinopril", "Chronic Kidney Disease", "Level A"),
    ("Furosemide", "Chronic Kidney Disease", "Level B"),
    # Asthma
    ("Salbutamol", "Asthma", "Level A"),
    # Major Depressive Disorder
    ("Sertraline", "Major Depressive Disorder", "Level A"),
    # Hypothyroidism
    ("Levothyroxine", "Hypothyroidism", "Level A"),
    # Atrial Fibrillation
    ("Warfarin", "Atrial Fibrillation", "Level A"),
    ("Amiodarone", "Atrial Fibrillation", "Level B"),
    # COPD
    ("Tiotropium", "Chronic Obstructive Pulmonary Disease", "Level A"),
    ("Salbutamol", "Chronic Obstructive Pulmonary Disease", "Level A"),
    # Osteoarthritis
    ("Ibuprofen", "Osteoarthritis", "Level A"),
]


# DRUG → DRUG  (INTERACTS_WITH) with severity and description
DRUG_INTERACTIONS = [
    {
        "drug_a": "Metformin",
        "drug_b": "Aspirin",
        "severity": "Mild",
        "description": "Aspirin may slightly enhance the hypoglycaemic effect of metformin.",
    },
    {
        "drug_a": "Warfarin",
        "drug_b": "Aspirin",
        "severity": "Major",
        "description": "Concurrent use significantly increases bleeding risk due to combined anticoagulation and platelet inhibition.",
    },
    {
        "drug_a": "Warfarin",
        "drug_b": "Ibuprofen",
        "severity": "Major",
        "description": "NSAIDs displace warfarin from plasma proteins and inhibit platelet function, markedly increasing bleeding risk.",
    },
    {
        "drug_a": "Warfarin",
        "drug_b": "Amiodarone",
        "severity": "Major",
        "description": "Amiodarone inhibits CYP2C9 and CYP3A4, substantially increasing warfarin plasma levels and INR.",
    },
    {
        "drug_a": "Lisinopril",
        "drug_b": "Furosemide",
        "severity": "Moderate",
        "description": "May cause first-dose hypotension; requires blood pressure monitoring when initiated together.",
    },
    {
        "drug_a": "Lisinopril",
        "drug_b": "Ibuprofen",
        "severity": "Moderate",
        "description": "NSAIDs can reduce the antihypertensive effect of ACE inhibitors and worsen renal function.",
    },
    {
        "drug_a": "Metformin",
        "drug_b": "Furosemide",
        "severity": "Moderate",
        "description": "Furosemide may increase metformin plasma levels, raising the risk of lactic acidosis.",
    },
    {
        "drug_a": "Aspirin",
        "drug_b": "Ibuprofen",
        "severity": "Moderate",
        "description": "Ibuprofen can competitively inhibit the antiplatelet effect of low-dose aspirin.",
    },
    {
        "drug_a": "Atorvastatin",
        "drug_b": "Amiodarone",
        "severity": "Moderate",
        "description": "Amiodarone inhibits CYP3A4, increasing atorvastatin exposure and risk of myopathy.",
    },
    {
        "drug_a": "Sertraline",
        "drug_b": "Aspirin",
        "severity": "Moderate",
        "description": "SSRIs combined with antiplatelet agents increase the risk of gastrointestinal bleeding.",
    },
    {
        "drug_a": "Clopidogrel",
        "drug_b": "Omeprazole",
        "severity": "Moderate",
        "description": "Omeprazole inhibits CYP2C19, reducing activation of clopidogrel and its antiplatelet effect.",
    },
]


# DISEASE → DISEASE  (COMORBID_WITH)
COMORBIDITIES = [
    ("Type 2 Diabetes Mellitus", "Hypertension"),
    ("Type 2 Diabetes Mellitus", "Coronary Artery Disease"),
    ("Type 2 Diabetes Mellitus", "Chronic Kidney Disease"),
    ("Hypertension", "Coronary Artery Disease"),
    ("Hypertension", "Atrial Fibrillation"),
    ("Coronary Artery Disease", "Atrial Fibrillation"),
    ("Chronic Kidney Disease", "Hypertension"),
    ("Major Depressive Disorder", "Hypothyroidism"),
    ("Chronic Obstructive Pulmonary Disease", "Asthma"),
]


# GENES  (name, full_name, associated_diseases)
GENES = [
    {
        "name": "TCF7L2",
        "full_name": "Transcription Factor 7 Like 2",
        "diseases": ["Type 2 Diabetes Mellitus"],
    },
    {
        "name": "ACE",
        "full_name": "Angiotensin-Converting Enzyme",
        "diseases": ["Hypertension", "Coronary Artery Disease", "Chronic Kidney Disease"],
    },
    {
        "name": "APOE",
        "full_name": "Apolipoprotein E",
        "diseases": ["Coronary Artery Disease"],
    },
    {
        "name": "NPPA",
        "full_name": "Natriuretic Peptide A",
        "diseases": ["Atrial Fibrillation", "Hypertension"],
    },
    {
        "name": "HTR2A",
        "full_name": "5-Hydroxytryptamine Receptor 2A",
        "diseases": ["Major Depressive Disorder"],
    },
    {
        "name": "THRB",
        "full_name": "Thyroid Hormone Receptor Beta",
        "diseases": ["Hypothyroidism"],
    },
]


def generate():
    dataset = {
        "diseases": DISEASES,
        "symptoms": SYMPTOMS,
        "drugs": DRUGS,
        "disease_symptoms": DISEASE_SYMPTOMS,
        "drug_treats": DRUG_TREATS,
        "drug_interactions": DRUG_INTERACTIONS,
        "comorbidities": COMORBIDITIES,
        "genes": GENES,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "processed")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "synthetic_medical_data.json")

    with open(out_path, "w") as f:
        json.dump(dataset, f, indent=2)

    print(f"[OK] Synthetic data written to {out_path}")
    print(f"     Diseases:      {len(DISEASES)}")
    print(f"     Symptoms:      {len(SYMPTOMS)}")
    print(f"     Drugs:         {len(DRUGS)}")
    print(f"     D->S edges:    {len(DISEASE_SYMPTOMS)}")
    print(f"     Drug treats:   {len(DRUG_TREATS)}")
    print(f"     Interactions:  {len(DRUG_INTERACTIONS)}")
    print(f"     Comorbidities: {len(COMORBIDITIES)}")
    print(f"     Genes:         {len(GENES)}")
    return dataset


if __name__ == "__main__":
    generate()
