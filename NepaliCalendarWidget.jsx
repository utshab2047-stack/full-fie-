import React, { useState, useEffect } from 'react';
import NepaliDate from 'nepali-date-converter';
import { ChevronLeft, ChevronRight, Calendar } from 'lucide-react';

const NepaliCalendarWidget = () => {
    const [currentDate, setCurrentDate] = useState(new NepaliDate());
    const [viewDate, setViewDate] = useState(new NepaliDate());

    // Constants
    const weekDays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const months = [
        "Baisakh", "Jestha", "Ashadh", "Shrawan", "Bhadra", "Ashwin",
        "Kartik", "Mangsir", "Poush", "Magh", "Falgun", "Chaitra"
    ];
    const monthsDev = [
        "बैशाख", "जेठ", "असार", "साउन", "भदौ", "असोज",
        "कार्तिक", "मंसिर", "पुष", "माघ", "फागुन", "चैत"
    ];
    const digitMap = {
        '0': '०', '1': '१', '2': '२', '3': '३', '4': '४',
        '5': '५', '6': '६', '7': '७', '8': '८', '9': '९'
    };

    const toNepaliDigits = (num) => {
        return num.toString().split('').map(d => digitMap[d] || d).join('');
    };

    // Helper to get calendar grid
    const getDaysInMonth = (year, month) => {
        // nepali-date-converter doesn't expose a static map easily often, 
        // but instance methods work.
        // Easiest way: construct date for month start, iterate until month changes?
        // Or use .getBsMonthDays()?
        // checking library docs from memory: usually strictly calculated.
        // Let's rely on basic iteration which is safe.
        const d = new NepaliDate(year, month, 1);
        // Wait, constructor (y, m, d). m is 0-11.

        // Note: library might not have method for days in month directly exposed in all versions.
        // Hack: go to day 32 and see if it rolls over?
        // Better: Create Month+1 day 1, subtract 1 day?
        // No, library handles overflow.
        // Let's try simplified approach:
        // Poush 2081 -> 29 days?
        // We can map visually.

        // Actually creating a map for the view:
        const days = [];
        const firstDay = new NepaliDate(year, month, 1);
        const startWeekDay = firstDay.getDay(); // 0 = Sun

        // Previous month padding
        for (let i = 0; i < startWeekDay; i++) {
            days.push(null);
        }

        // Current month days
        // Iterate up to 32 days, check if month changes
        for (let i = 1; i <= 32; i++) {
            const check = new NepaliDate(year, month, i);
            if (check.getMonth() !== month) break;
            days.push(check);
        }
        return days;
    };

    const days = getDaysInMonth(viewDate.getYear(), viewDate.getMonth());

    const handlePrevMonth = () => {
        let m = viewDate.getMonth() - 1;
        let y = viewDate.getYear();
        if (m < 0) { m = 11; y -= 1; }
        setViewDate(new NepaliDate(y, m, 1));
    };

    const handleNextMonth = () => {
        let m = viewDate.getMonth() + 1;
        let y = viewDate.getYear();
        if (m > 11) { m = 0; y += 1; }
        setViewDate(new NepaliDate(y, m, 1));
    };

    const isToday = (d) => {
        return d && d.getYear() === currentDate.getYear() &&
            d.getMonth() === currentDate.getMonth() &&
            d.getDate() === currentDate.getDate();
    };

    // Market Status Logic (Simplified for Visual)
    const isWeekend = (d) => {
        if (!d) return false;
        const day = d.getDay();
        return day === 5 || day === 4; // Sat & Fri closed? User said Fri/Sat.
    };

    return (
        <div className="bg-white rounded-lg shadow-md border border-gray-400 overflow-hidden max-w-sm mx-auto">
            {/* Header Section */}
            <div className="bg-[#e0e0e0] p-2">
                <div className="flex justify-between items-center bg-[#e0e0e0] px-2 py-1 border-b border-gray-300">
                    <button onClick={handlePrevMonth} className="px-2 py-0.5 bg-white border border-gray-400 rounded text-black hover:bg-gray-100 text-sm">&lt;</button>
                    <div className="text-center">
                        <div className="text-lg font-bold text-gray-800 tracking-wide">
                            {toNepaliDigits(viewDate.getYear())}/<span className="text-sm">{viewDate.getYear() + 57}</span>
                        </div>
                        <div className="text-xl font-bold text-[#666] flex items-center justify-center gap-2">
                            {monthsDev[viewDate.getMonth()]} <span className="text-xs font-normal">({months[viewDate.getMonth()].toUpperCase().slice(0, 3)}/{months[(viewDate.getMonth() + 1) % 12].toUpperCase().slice(0, 3)})</span>
                        </div>
                    </div>
                    <button onClick={handleNextMonth} className="px-2 py-0.5 bg-white border border-gray-400 rounded text-black hover:bg-gray-100 text-sm">&gt;</button>
                </div>

                {/* Week Days Header */}
                <div className="grid grid-cols-7 mt-1 border-b border-gray-300 bg-[#f9f9f9]">
                    {["आइत", "सोम", "मंगल", "बुध", "बिही", "शुक्र", "शनि"].map((d, i) => (
                        <div key={d} className={`text-center py-1 text-sm font-semibold ${i === 6 ? 'text-red-600' : 'text-green-700'}`}>
                            {d}वार
                        </div>
                    ))}
                </div>
            </div>

            {/* Calendar Grid */}
            <div className="w-full bg-[#f4f4f4] border-t border-gray-400 p-1">
                <div className="grid grid-cols-7 gap-px bg-gray-300 border border-gray-300">
                    {days.map((d, i) => {
                        if (!d) return <div key={i} className="bg-[#f4f4f4] min-h-[60px]"></div>;

                        const isSat = d.getDay() === 6;
                        // const isFri = d.getDay() === 4; 
                        const today = isToday(d);
                        const dayNum = d.getDate();
                        const dayNumNep = toNepaliDigits(dayNum);

                        // Mock Events for demo (Poush 2081)
                        let event = "";
                        if (viewDate.getMonth() === 8) { // Poush
                            if (dayNum === 10) event = "क्रिसमस";
                            if (dayNum === 15) event = "तमु ल्होसार";
                            if (dayNum === 27) event = "पृथ्वी जयन्ती";
                        }

                        // Text Color Logic: Sat = Red, Others = Green (as per screenshot)
                        const textColor = isSat ? 'text-red-500' : 'text-green-700';
                        const bgColor = today ? 'bg-blue-100' : 'bg-[#f4f4f4]';

                        return (
                            <div
                                key={i}
                                className={`
                                    ${bgColor} min-h-[60px] p-1 flex flex-col items-center justify-start relative hover:bg-white
                                `}
                            >
                                <span className={`text-2xl font-bold ${textColor} leading-none mt-1`}>
                                    {dayNumNep}
                                </span>
                                {event && (
                                    <span className="text-[9px] text-red-500 font-medium text-center leading-tight mt-1">
                                        {event}
                                    </span>
                                )}
                                {/* English Date small corner */}
                                <span className="absolute top-1 right-1 text-[8px] text-gray-400">
                                    {/* Approx AD date calc or just hide to keep clean like screenshot */}
                                </span>
                            </div>
                        );
                    })}
                </div>
            </div >
        </div >
    );
};

export default NepaliCalendarWidget;
