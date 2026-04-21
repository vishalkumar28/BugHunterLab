export function SectionCard({ title, eyebrow, children }: Readonly<{ title: string; eyebrow?: string; children: React.ReactNode }>) {
  return (
    <section className="panel">
      {eyebrow ? <p className="eyebrow mb-3">{eyebrow}</p> : null}
      <h2 className="font-display text-2xl">{title}</h2>
      <div className="mt-4">{children}</div>
    </section>
  );
}