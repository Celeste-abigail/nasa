import { useTranslation } from "react-i18next";

import type { Recommendation } from "../../lib/types";
import { RecommendationPanel } from "../shell/RecommendationPanel";

interface Props {
  recommendation: Recommendation;
}

export function RecommendationsPanel({ recommendation }: Props) {
  const { t } = useTranslation();

  return (
    <RecommendationPanel
      severity={recommendation.level}
      title={`${t("exercise.section")} · ${recommendation.title}`}
      items={recommendation.items}
      note={recommendation.disclaimer}
    />
  );
}
