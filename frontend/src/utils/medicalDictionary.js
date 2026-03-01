// Medical terminology simplified for patients

export const medicalDictionary = {
    // Blood Chemistry
    'glucose': 'Blood sugar - Energy source for your body',
    'hemoglobin': 'Protein in red blood cells that carries oxygen',
    'hematocrit': 'Percentage of blood that is red blood cells',
    'platelet': 'Blood cells that help with clotting',
    'wbc': 'White blood cells - Your immune system defenders',
    'rbc': 'Red blood cells - Oxygen carriers in your blood',

    // Lipids
    'cholesterol': 'Fat-like substance, some good (HDL) and some bad (LDL)',
    'hdl': 'Good cholesterol - Helps remove bad cholesterol',
    'ldl': 'Bad cholesterol - Can clog arteries if too high',
    'triglycerides': 'Type of fat in blood - High levels increase heart risk',

    // Liver
    'alt': 'Liver enzyme - High levels may indicate liver stress',
    'ast': 'Liver enzyme - Can indicate liver or heart issues',
    'bilirubin': 'Waste product from red blood cell breakdown',
    'albumin': 'Protein made by liver - Indicates liver health',

    // Kidney
    'creatinine': 'Waste product filtered by kidneys',
    'bun': 'Blood urea nitrogen - Kidney function indicator',
    'egfr': 'How well kidneys filter waste from blood',

    // Thyroid
    'tsh': 'Thyroid stimulating hormone - Controls metabolism',
    't3': 'Thyroid hormone - Regulates body temperature and energy',
    't4': 'Thyroid hormone - Controls metabolism and growth',

    // Vitamins
    'vitamin d': 'Helps absorb calcium for strong bones and immune function',
    'vitamin b12': 'Important for nerve function and red blood cell production',
    'folate': 'B vitamin needed for cell growth and DNA production',

    // Inflammation
    'crp': 'C-reactive protein - Indicates inflammation in body',
    'esr': 'How fast red blood cells settle - Shows inflammation',

    // Hormones
    'testosterone': 'Male hormone - Also important for women in smaller amounts',
    'estrogen': 'Female hormone - Also present in men in smaller amounts',
    'cortisol': 'Stress hormone - Regulates metabolism and immune response',

    // General  
    'hemoglobin a1c': 'Average blood sugar over past 2-3 months',
    'ferritin': 'Your body\'s iron storage battery',
    'sodium': ' Electrolyte for nerve and muscle function',
    'potassium': 'Electrolyte for heart rhythm and muscle function',
}

export const getMedicalExplanation = (term) => {
    const normalized = term.toLowerCase().trim()

    // Direct match
    if (medicalDictionary[normalized]) {
        return medicalDictionary[normalized]
    }

    // Partial match
    for (const [key, value] of Object.entries(medicalDictionary)) {
        if (normalized.includes(key) || key.includes(normalized)) {
            return value
        }
    }

    // No match found
    return 'Medical term - Ask HealthLoom AI for more information'
}

export default medicalDictionary
