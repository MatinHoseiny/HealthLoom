import { motion } from "framer-motion";

const BlurInText = ({ word, className }) => {
    return (
        <motion.h1
            initial={{ filter: "blur(20px)", opacity: 0, y: -20 }}
            animate={{ filter: "blur(0px)", opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: "easeOut" }}
            className={className}
        >
            {word}
        </motion.h1>
    );
};

export default BlurInText;
