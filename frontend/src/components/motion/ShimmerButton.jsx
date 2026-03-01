import { motion } from 'framer-motion'
import './ShimmerButton.css'

export default function ShimmerButton({ children, onClick, className = '', variant = 'primary' }) {
    return (
        <motion.button
            className={`shimmer-button shimmer-button-${variant} ${className}`}
            onClick={onClick}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            transition={{ duration: 0.2 }}
        >
            <span className="shimmer-button-content">{children}</span>
            <div className="shimmer-effect"></div>
        </motion.button>
    )
}
