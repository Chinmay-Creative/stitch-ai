export default function StitchControls() {
  return (
    <aside className="rounded-lg border border-neutral-200 bg-white p-5">
      <h2 className="text-lg font-semibold text-neutral-950">Stitch controls</h2>
      <label className="mt-5 block text-sm font-medium text-neutral-700">
        Density
        <input type="range" min="1" max="10" defaultValue="5" className="mt-2 w-full" />
      </label>
      <label className="mt-5 block text-sm font-medium text-neutral-700">
        Thread colors
        <input
          type="number"
          min="1"
          max="24"
          defaultValue="6"
          className="mt-2 h-10 w-full rounded-md border border-neutral-300 px-3"
        />
      </label>
    </aside>
  );
}
