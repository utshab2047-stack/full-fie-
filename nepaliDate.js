export const AD_TO_BS = [
    { year: 2080, months: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 30] }, // 2023-2024
    { year: 2081, months: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 30, 30] }, // 2024-2025 (Current)
    { year: 2082, months: [31, 32, 32, 31, 31, 30, 30, 30, 29, 30, 30, 30] }  // 2025-2026
];

export const NEPAL_MONTHS = [
    "Baisakh", "Jestha", "Ashadh", "Shrawan", "Bhadra", "Ashwin",
    "Kartik", "Mangsir", "Poush", "Magh", "Falgun", "Chaitra"
];

export const NEPAL_DAYS = [
    "Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"
];

// Reference point: 1st Baisakh 2081 is 2024-04-13
const REF_BS = { y: 2081, m: 0, d: 1 };
const REF_AD = new Date("2024-04-13T00:00:00");

export const getNepaliDate = (date = new Date()) => {
    // Simple approximation or hardcoded logic for MVP if library unavailable
    // For robustness, calculate diff days from REF_AD
    const diffTime = date.getTime() - REF_AD.getTime();
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

    let daysCount = diffDays;
    let currentY = REF_BS.y;
    let currentM = REF_BS.m;
    let currentD = REF_BS.d;

    // Moving forward or backward... lets implemented forward only for 2081+ for now
    // Real implementation needs full map.
    // Assuming 2081 for now as per current date

    // Actually, let's try to assume we can just use the backend API provided date for "Today"
    // and build the grid around it? 
    // No, navigation needs logic.

    return { year: 2081, month: 8, day: 27, str: "2081 Poush 27" }; // Placeholder
};
