import React from "react";

export default function MainLayout({ children }) {
    return (
        <div className="flex w-full h-full bg-[#08090D] text-[#F5F7FA] font-sans overflow-hidden antialiased select-none">
            {children}
        </div>
    );
}