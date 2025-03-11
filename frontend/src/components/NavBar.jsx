import React from "react";
import logo from "../assets/swordlogo.jpg";

const NavBar = () => {
  return (
    <>
      <div className="absolute top-0 flex h-20 w-full items-center justify-center bg-[#225688]">
        <div className="max-w-screen-xl flex flex-1">
          <img src={logo} width="150px" alt="logo" className="h-auto" />
          <div className="flex flex-1 justify-end items-center">
            <ul className="flex text-white space-x-12 text-xl">
              <li>Home</li>
              <li>Pricing</li>
              <li>About Us</li>
            </ul>
          </div>
        </div>
      </div>
    </>
  );
};

export default NavBar;
