import React from "react";
import ChatWidget from "../components/ChatWidget";
import NavBar from "../components/NavBar";
import Hero from "../components/Hero";

const Homepage = () => {
  return (
    <>
      <div className="flex justify-center items-center h-dvh w-full bg-radial from-[#225688] from-10% to-[#cce6ff] to-300%">
        <NavBar />
        <Hero />
        <ChatWidget />
      </div>
    </>
  );
};

export default Homepage;
