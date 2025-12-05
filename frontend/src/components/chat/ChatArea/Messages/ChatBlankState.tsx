'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'

const EXTERNAL_LINKS = {
  github: 'https://github.com/Krrish777/AI-Engineer-Internship-Task',
  linkedin: 'https://www.linkedin.com/in/krish-sharma-3375b927b/'
}

interface ActionButtonProps {
  href: string
  variant?: 'primary'
  text: string
}

const ActionButton = ({ href, variant, text }: ActionButtonProps) => {
  const baseStyles =
    'px-4 py-2 text-sm transition-colors font-dmmono tracking-tight'
  const variantStyles = {
    primary: 'border border-border hover:bg-neutral-800 rounded-xl'
  }

  return (
    <Link
      href={href}
      target="_blank"
      className={`${baseStyles} ${variant ? variantStyles[variant] : ''}`}
    >
      {text}
    </Link>
  )
}

const ChatBlankState = () => {
  return (
    <section
      className="flex flex-col items-center text-center font-geist"
      aria-label="Welcome message"
    >
      <div className="flex max-w-3xl flex-col gap-y-8">
        <motion.h1
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="text-3xl font-[600] tracking-tight"
        >
          <div className="flex flex-col items-center justify-center gap-y-2">
            <span className="flex items-center gap-x-2 font-[600]">
              Personality-Driven AI Assistant
            </span>
            <span className="flex items-center gap-x-2 text-lg font-normal text-muted-foreground">
              Built with Next.js & AgentOS
            </span>
          </div>
        </motion.h1>
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.5 }}
          className="flex justify-center gap-4"
        >
          <ActionButton
            href={EXTERNAL_LINKS.github}
            variant="primary"
            text="VIEW SOURCE CODE"
          />
          <ActionButton href={EXTERNAL_LINKS.linkedin} text="CONNECT ON LINKEDIN" />
        </motion.div>
      </div>
    </section>
  )
}

export default ChatBlankState
