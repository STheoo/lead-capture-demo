import React, { useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { RiChatAiFill, RiCloseLine, RiSendPlaneLine, RiAttachment2, RiFileTextLine, RiCloseFill } from "react-icons/ri";

const ChatWidget = () => {
    const [isOpen, setIsOpen] = useState(false);
    const fileInputRef = useRef(null);
    const [messages, setMessages] = useState([
        {
            content: "Hello there. I work for Sword and here to help answer all your questions! 😊",
            isUser: false,
        },
    ]);
    const [file, setFile] = useState(null);
    const [isLoading, setIsLoading] = useState(false);

    const [inputText, setInputText] = useState("");

    const handleFileChange = (event) => {
        setFile(event.target.files[0]);
    };

    const handleAttachClick = () => {
        // Trigger click on the hidden file input element
        fileInputRef.current.click();
    };

    const handleRemoveFile = () => {
        setFile(null);
        // Reset the file input
        if (fileInputRef.current) {
            fileInputRef.current.value = "";
        }
    };

    const handleSend = async () => {
        if (!inputText.trim()) return;

        // Add user message
        const newMessages = [...messages, { content: inputText, isUser: true }];
        setMessages(newMessages);
        setInputText("");

        // Set loading state to true before API call
        setIsLoading(true);

        if (file) {
            try {
                const formData = new FormData();
                formData.append("file", file);
                // Call your FastAPI endpoint
                const response = await fetch(`http://localhost:8000/call-graph-file?query=${encodeURIComponent(inputText)}&thread_id=1`, {
                    method: "POST",
                    body: formData,
                });

                const data = await response.json();
                setMessages([...newMessages, { content: data, isUser: false }]);
            } catch (error) {
                console.error("API Error:", error);
                setMessages([...newMessages, { content: "Connection error", isUser: false }]);
            } finally {
                setFile(null);
                if (fileInputRef.current) {
                    fileInputRef.current.value = "";
                }
                setIsLoading(false);
            }
        } else {
            try {
                // Call your FastAPI endpoint
                const response = await fetch(`http://localhost:8000/call-graph?query=${encodeURIComponent(inputText)}&thread_id=1`);

                const data = await response.json();
                setMessages([...newMessages, { content: data, isUser: false }]);
            } catch (error) {
                console.error("API Error:", error);
                setMessages([...newMessages, { content: "Connection error", isUser: false }]);
            } finally {
                setIsLoading(false);
            }
        }
    };

    const truncateFilename = (name, maxLength = 60) => {
        if (!name) return "";
        if (name.length <= maxLength) return name;

        const extension = name.split(".").pop();
        const baseName = name.substring(0, name.length - extension.length - 1);

        return baseName.substring(0, maxLength - extension.length - 3) + "..." + extension;
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
                        <div className="flex h-[600px] flex-col">
                            {/* Header - New Addition */}
                            <div className="bg-blue-950 text-white p-4 rounded-t-2xl shadow-md">
                                <div className="flex items-center space-x-3">
                                    <div>
                                        <h3 className="font-bold text-lg">Sword Assistant</h3>
                                        <div className="flex items-center text-xs text-blue-200">
                                            <span className="flex h-2 w-2 relative mr-2">
                                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                                                <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                                            </span>
                                            Online
                                        </div>
                                    </div>
                                </div>
                            </div>
                            {/* Messages Container */}
                            <div className="flex-1 space-y-3 overflow-y-auto p-4">
                                <AnimatePresence initial={false}>
                                    {messages.map((message, index) => (
                                        <motion.div
                                            key={index}
                                            className={`flex ${message.isUser ? "justify-end" : "justify-start"}`}
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
                                    {isLoading && (
                                        <motion.div
                                            className="flex justify-start"
                                            initial={{ opacity: 0, y: 10 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            transition={{ duration: 0.2 }}
                                        >
                                            <div className="max-w-[75%] rounded-lg rounded-bl-none bg-gray-100 p-2 text-xs text-gray-800">
                                                <div className="flex items-center gap-1">
                                                    <span className="mr-1">Typing</span>
                                                    <span className="flex space-x-1">
                                                        <motion.div
                                                            className="h-2 w-2 rounded-full bg-gray-500"
                                                            animate={{
                                                                scale: [1, 1.2, 1],
                                                                opacity: [0.6, 1, 0.6],
                                                            }}
                                                            transition={{
                                                                duration: 1,
                                                                repeat: Infinity,
                                                                repeatType: "loop",
                                                            }}
                                                        />
                                                        <motion.div
                                                            className="h-2 w-2 rounded-full bg-gray-500"
                                                            animate={{
                                                                scale: [1, 1.2, 1],
                                                                opacity: [0.6, 1, 0.6],
                                                            }}
                                                            transition={{
                                                                duration: 1,
                                                                repeat: Infinity,
                                                                repeatType: "loop",
                                                                delay: 0.3,
                                                            }}
                                                        />
                                                        <motion.div
                                                            className="h-2 w-2 rounded-full bg-gray-500"
                                                            animate={{
                                                                scale: [1, 1.2, 1],
                                                                opacity: [0.6, 1, 0.6],
                                                            }}
                                                            transition={{
                                                                duration: 1,
                                                                repeat: Infinity,
                                                                repeatType: "loop",
                                                                delay: 0.6,
                                                            }}
                                                        />
                                                    </span>
                                                </div>
                                            </div>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>

                            {/* Input Area */}
                            <div className="border-t p-4">
                                <AnimatePresence>
                                    {file && (
                                        <motion.div
                                            className="flex items-center bg-blue-100 text-blue-800 text-xs p-2 rounded mb-4"
                                            initial={{ opacity: 0, y: 10 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            exit={{ opacity: 0, y: 10 }}
                                        >
                                            <RiFileTextLine className="h-4 w-4 mr-1" />
                                            <span className="flex-1 truncate">{truncateFilename(file.name)}</span>
                                            <button onClick={handleRemoveFile} className="ml-2 text-blue-700 hover:text-blue-900">
                                                <RiCloseFill className="h-4 w-4" />
                                            </button>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                                <div className="flex gap-2">
                                    <input
                                        type="file"
                                        ref={fileInputRef}
                                        className="hidden"
                                        onChange={handleFileChange}
                                        accept="pdf/*" // Adjust the accepted file types as needed
                                    />
                                    <motion.button
                                        onClick={handleAttachClick}
                                        className={`relative flex h-10 w-10 items-center justify-center rounded-full p-3 text-white ${
                                            file ? "bg-blue-700" : "bg-blue-950"
                                        }`}
                                        whileHover={{ scale: 1.05 }}
                                        whileTap={{ scale: 0.95 }}
                                    >
                                        <RiAttachment2 className="h-10 w-10" />
                                        {/* Badge indicator when file is selected */}
                                        {file && (
                                            <div className="absolute -top-2 -right-2 h-5 w-5 bg-green-500 rounded-full flex items-center justify-center border-2 border-white">
                                                <span className="text-white text-[11px] font-medium">1</span>
                                            </div>
                                        )}
                                    </motion.button>
                                    <input
                                        value={inputText}
                                        onChange={(e) => setInputText(e.target.value)}
                                        onClick={(e) => e.key === "Enter" && handleSend()}
                                        placeholder="Type your message..."
                                        className="w-full rounded-full border px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-950"
                                        disabled={isLoading}
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
