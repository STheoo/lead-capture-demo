import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { RiChatAiFill, RiCloseLine, RiSendPlaneLine } from "react-icons/ri";

const ChatWidget = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState("");

  const handleSend = async () => {
    if (!inputText.trim()) return;

    // Add user message
    const newMessages = [...messages, { content: inputText, isUser: true }];
    setMessages(newMessages);
    setInputText("");

    try {
      // Call your FastAPI endpoint
      const response = await fetch(
        `http://localhost:8000/call-agent?query=${encodeURIComponent(
          inputText
        )}&user_id=1`
      );

      const data = await response.json();
      setMessages([...newMessages, { content: data, isUser: false }]);
    } catch (error) {
      console.error("API Error:", error);
      setMessages([
        ...newMessages,
        { content: "Connection error", isUser: false },
      ]);
    }
  };

  return (
    <div className="fixed right-10 bottom-10 z-50">
      <motion.button
        onClick={() => setIsOpen(!isOpen)}
        className="flex h-16 w-16 cursor-pointer items-center rounded-full bg-blue-950 p-4 text-white"
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        <AnimatePresence className="h-full w-full" initial={false}>
          {isOpen ? (
            <motion.div
              className="h-10 w-10 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2"
              key="close"
              initial={{ rotate: -90, opacity: 0 }}
              animate={{ rotate: 0, opacity: 1 }}
              exit={{ rotate: 90, opacity: 0 }}
              transition={{ duration: 0.2 }}
            >
              <RiCloseLine className="h-full w-full" />
            </motion.div>
          ) : (
            <motion.div
              className="h-10 w-10 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2"
              key="chat"
              initial={{ scale: 1, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
            >
              <RiChatAiFill className="h-full w-full" />
            </motion.div>
          )}
        </AnimatePresence>
      </motion.button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            className="absolute right-20 bottom-0 w-[500px] overflow-hidden rounded-2xl bg-white shadow-xl"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            transition={{ type: "spring", stiffness: 1000, damping: 100 }}
          >
            <div className="flex h-96 flex-col">
              {/* Messages Container */}
              <div className="flex-1 space-y-3 overflow-y-auto p-4">
                <AnimatePresence initial={false}>
                  {messages.map((message, index) => (
                    <motion.div
                      key={index}
                      className={`flex ${
                        message.isUser ? "justify-end" : "justify-start"
                      }`}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, x: message.isUser ? 50 : -50 }}
                      transition={{ duration: 0.2 }}
                    >
                      <div
                        className={`max-w-[75%] rounded-lg p-2 ${
                          message.isUser
                            ? "rounded-br-none bg-blue-950 text-xs text-white"
                            : "rounded-bl-none bg-gray-100 text-xs text-gray-800"
                        }`}
                      >
                        {message.content}
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>

              {/* Input Area */}
              <div className="border-t p-4">
                <div className="flex gap-2">
                  <input
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    onKeyPress={(e) => e.key === "Enter" && handleSend()}
                    placeholder="Type your message..."
                    className="w-full rounded-full border px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-950"
                  />
                  <motion.button
                    onClick={handleSend}
                    className="flex h-10 w-10 items-center justify-center rounded-full p-3 bg-blue-950 text-white"
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    disabled={!inputText.trim()}
                  >
                    <RiSendPlaneLine className="h-10 w-10" />
                  </motion.button>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ChatWidget;
