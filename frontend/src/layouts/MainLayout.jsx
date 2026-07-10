function MainLayout({ children }) {
    return (
        <div className="flex h-screen bg-[#343541] text-white">
            {children}
        </div>
    );
}

export default MainLayout;