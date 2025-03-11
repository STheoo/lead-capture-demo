import React from "react";
import { motion, AnimatePresence } from "framer-motion";

const Hero = () => {
  return (
    <>
      <div className="flex h-auto w-full max-w-screen-xl">
        <motion.div
          className="flex-1 text-6xl p-8 font-bold text-white"
          initial={{ y: -150 }}
          animate={{ y: 0 }}
          transition={{ type: "spring", stiffness: 300, damping: 40 }}
        >
          One place for all your business software solutions.
        </motion.div>
        <motion.div
          className="flex-1 text-6xl p-8 text-white text-center border-[1px] border-blue-100"
          initial={{ y: -150 }}
          animate={{ y: 0 }}
          transition={{ type: "spring", stiffness: 150, damping: 40 }}
        >
          Websites <br /> Mobile Apps <br /> AI Automations
        </motion.div>
      </div>
    </>
  );
};

export default Hero;
