import Sidebar from "../components/Sidebar";
import Navbar from "../components/Navbar";
import ChatBox from "../components/ChatBox";
import MainLayout from "../layouts/MainLayout";

function Home() {
    return (
        <MainLayout>

            <Sidebar />

            <div className="flex-1 flex flex-col">

                <Navbar />

                <div className="flex-1 overflow-y-auto">

                    <ChatBox />

                </div>

            </div>

        </MainLayout>
    );
}

export default Home;