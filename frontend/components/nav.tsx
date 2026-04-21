import Link from "next/link";

const links = [
  ["Dashboard", "/"],
  ["Scope Analyzer", "/scope-analyzer"],
  ["Recon Results", "/recon-results"],
  ["Attack Surface", "/attack-surface-map"],
  ["Testing Checklist", "/testing-checklist"],
  ["Bug Guide", "/bug-testing-guide"],
  ["Evidence", "/evidence-manager"],
  ["PoC", "/poc-generator"],
  ["Reports", "/report-builder"],
] as const;

export function Nav() {
  return (
    <nav className="flex flex-wrap gap-3 text-sm" aria-label="Main navigation">
      {links.map(([label, href]) => (
        <Link
          className="rounded-full border border-black/10 bg-white/70 px-4 py-2 transition hover:-translate-y-0.5 hover:bg-white"
          href={href}
          key={href}
        >
          {label}
        </Link>
      ))}
    </nav>
  );
}