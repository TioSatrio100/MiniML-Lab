import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'

const links = [
  { href: '#how', label: 'How it works' },
  { href: '#features', label: 'Features' },
]

export default function Navbar() {
  return (
    <header className="sticky top-0 z-50 border-b border-border bg-background/85 backdrop-blur-md">
      <div className="mx-auto flex h-16 w-full max-w-7xl items-center justify-between px-6">
        <Link to="/" className="flex items-center gap-2.5">
          <span className="flex size-7 items-center justify-center rounded-lg bg-primary font-mono text-sm font-bold text-primary-foreground">
            M
          </span>
          <span className="text-sm font-semibold tracking-tight text-foreground">MiniML Lab</span>
        </Link>

        <nav className="hidden items-center gap-7 sm:flex">
          {links.map((l) => (
            <a
              key={l.href}
              href={l.href}
              className="text-sm text-muted-foreground transition-colors hover:text-foreground"
            >
              {l.label}
            </a>
          ))}
        </nav>

        <Button asChild>
          <Link to="/app">Open dashboard</Link>
        </Button>
      </div>
    </header>
  )
}
