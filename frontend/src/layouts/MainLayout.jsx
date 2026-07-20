function MainLayout({ children }) {
    return (
        <div className="flex h-screen bg-[#0B0F19] text-white font-sans overflow-hidden antialiased">
            {children}
        </div>
    );
}

export default MainLayout;