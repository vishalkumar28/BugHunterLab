import { DashboardView } from "../components/dashboard-view";
import { LearningStrip } from "../components/learning-strip";

export default function Page() {
  return (
    <>
      <DashboardView />
      <div className="-mt-6 px-4 pb-8 sm:px-6 lg:px-8" suppressHydrationWarning>
        <div className="mx-auto max-w-7xl" suppressHydrationWarning>
          <LearningStrip />
        </div>
      </div>
    </>
  );
}