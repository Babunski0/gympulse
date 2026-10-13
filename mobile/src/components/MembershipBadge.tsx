import { t } from "@/i18n/sr";
import type { MembershipStatus } from "@/lib/api";

import { Badge } from "./ui";

export function MembershipBadge({ status }: { status: MembershipStatus }) {
  if (status === "active") return <Badge label={t.statusActive} tone="success" />;
  if (status === "pending") return <Badge label={t.statusPending} tone="warning" />;
  return <Badge label={t.statusRejected} tone="muted" />;
}
