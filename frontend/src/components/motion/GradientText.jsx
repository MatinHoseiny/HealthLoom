import { motion } from 'framer-motion'
import './GradientText.css'

export default function GradientText({ children, className = '', gradient = 'primary' }) {
    const gradients = {
        primary: 'linear-gradient(90deg, #06b6d4 0%, #3b82f6 50%, #a855f7 100%)',
        success: 'linear-gradient(90deg, #10b981 0%, #059669 100%)',
        warning: 'linear-gradient(90deg, #f59e0b 0%, #ef4444 100%)',
        rainbow: 'linear-gradient(90deg, #06b6d4, #3b82f6, #a855f7, #ec4899, #ef4444)'
    }

    return (
        <motion.span
            className={`gradient-text ${className}`}
            style={{
                backgroundImage: gradients[gradient] || gradients.primary
            }}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
        >
            {children}
        </motion.span>
    )
}
