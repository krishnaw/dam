import { useState } from "react";
import { Share2, Copy, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog";
import { useCreateShare } from "@/api/useSharing";
import { toast } from "sonner";

interface ShareDialogProps {
  assetId: string;
}

export function ShareDialog({ assetId }: ShareDialogProps) {
  const [open, setOpen] = useState(false);
  const [expiresAt, setExpiresAt] = useState("");
  const [password, setPassword] = useState("");
  const [permissions, setPermissions] = useState("view");
  const [shareUrl, setShareUrl] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const createShare = useCreateShare();

  const handleCreate = () => {
    createShare.mutate(
      {
        asset_id: assetId,
        expires_at: expiresAt || undefined,
        password: password || undefined,
        permissions,
      },
      {
        onSuccess: (data) => {
          const url = data.shareUrl || `${window.location.origin}/share/${data.token}`;
          setShareUrl(url);
          toast.success("Share link created");
        },
      }
    );
  };

  const handleCopy = async () => {
    if (!shareUrl) return;
    await navigator.clipboard.writeText(shareUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleOpenChange = (next: boolean) => {
    setOpen(next);
    if (!next) {
      setShareUrl(null);
      setExpiresAt("");
      setPassword("");
      setPermissions("view");
      setCopied(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger
        render={
          <Button variant="outline" size="sm" className="gap-2" />
        }
      >
        <Share2 className="h-4 w-4" />
        Share
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Share Asset</DialogTitle>
        </DialogHeader>

        {!shareUrl ? (
          <div className="space-y-3">
            <div>
              <label className="text-xs font-medium text-muted-foreground">
                Expiry Date (optional)
              </label>
              <Input
                type="datetime-local"
                value={expiresAt}
                onChange={(e) => setExpiresAt(e.target.value)}
                className="mt-1"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-muted-foreground">
                Password (optional)
              </label>
              <Input
                type="password"
                placeholder="Leave empty for no password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-muted-foreground">
                Permissions
              </label>
              <select
                value={permissions}
                onChange={(e) => setPermissions(e.target.value)}
                className="mt-1 w-full rounded-md border bg-transparent px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
              >
                <option value="view">View only</option>
                <option value="download">View & Download</option>
              </select>
            </div>
          </div>
        ) : (
          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">
              Share link created. Copy and send it to others.
            </p>
            <div className="flex gap-2">
              <Input value={shareUrl} readOnly className="flex-1 text-sm" />
              <Button size="icon" onClick={handleCopy} variant="outline">
                {copied ? (
                  <Check className="h-4 w-4 text-green-500" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>
        )}

        <DialogFooter>
          {!shareUrl && (
            <Button onClick={handleCreate} disabled={createShare.isPending}>
              Create Link
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
