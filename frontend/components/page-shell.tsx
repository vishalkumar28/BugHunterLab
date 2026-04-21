import { Nav } from "./nav";

export function PageShell({ title, description, children }: Readonly<{ title: string; description: string; children: React.ReactNode }>) {
  return (
    <main className="mx-auto min-h-screen max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <header className="mb-8 space-y-4">
        <p className="eyebrow">BugHunterLab</p>
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="font-display text-4xl text-ink sm:text-5xl">{title}</h1>
            <p className="mt-3 max-w-3xl text-base text-ink/80">{description}</p>
          </div>
          <Nav />
        </div>
      </header>
      <div className="grid gap-6">{children}</div>
    </main>
  );
}