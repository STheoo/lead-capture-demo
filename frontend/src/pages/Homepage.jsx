import React from "react";
import logo from "../assets/swordlogo.jpg";

const Homepage = () => {
  return (
    <>
      <div className="flex justify-center items-center h-dvh w-full bg-radial from-[#225688] from-10% to-[#cce6ff] to-300%">
        <img src={logo} alt="logo" className="scale-25" />
      </div>
    </>
  );
};

export default Homepage;
