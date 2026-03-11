import { useState } from "react";
import { useParams } from "react-router-dom";
import { Download, Lock, FileIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useShareAccess } from "@/api/useSharing";
import { apiClient } from "@/api/client";
import { Skeleton } from "@/components/ui/skeleton";

export function ShareView() {
  const { token } = useParams<{ token: string }>();
  const [password, setPassword] = useState("");
  const [authenticated, setAuthenticated] = useState(false);
  const [authError, setAuthError] = useState(false);
  const { data: share, isLoading, error } = useShareAccess(token);

  const requiresPassword = share && !authenticated && error;

  const handleAuth = async () => {
    try {
      await apiClient.post(`/shares/${token}/verify`, { password });
      setAuthenticated(true);
      setAuthError(false);
    } catch {
      setAuthError(true);
    }
  };

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background p-4">
        <Card className="w-full max-w-lg">
          <CardContent>
            <Skeleton className="h-64 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (requiresPassword && !authenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background p-4">
        <Card className="w-full max-w-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Lock className="h-5 w-5" />
              Password Required
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Input
              type="password"
              placeholder="Enter password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleAuth()}
            />
            {authError && (
              <p className="text-sm text-destructive">Incorrect password</p>
            )}
            <Button className="w-full" onClick={handleAuth}>
              Access
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!share || (error && !requiresPassword)) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background p-4">
        <Card className="w-full max-w-sm">
          <CardContent className="py-8 text-center text-muted-foreground">
            <p className="text-lg font-medium">Link not found or expired</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const asset = share.asset;
  const isImage = asset?.mime_type?.startsWith("image/");
  const isVideo = asset?.mime_type?.startsWith("video/");
  const canDownload = share.permissions === "download";

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <Card className="w-full max-w-2xl">
        <CardHeader>
          <CardTitle className="text-lg">
            {asset?.original_filename ?? "Shared Asset"}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-center rounded-lg border bg-muted/30 p-4 min-h-[300px]">
            {isImage && asset && (
              <img
                src={`/api/shares/${token}/file`}
                alt={asset.original_filename}
                className="max-h-[500px] max-w-full object-contain"
              />
            )}
            {isVideo && asset && (
              <video
                src={`/api/shares/${token}/file`}
                controls
                className="max-h-[500px] max-w-full"
              />
            )}
            {!isImage && !isVideo && (
              <div className="text-center text-muted-foreground">
                <FileIcon className="mx-auto mb-2 h-12 w-12" />
                <p className="font-medium">{asset?.original_filename}</p>
                <p className="text-sm">{asset?.mime_type}</p>
              </div>
            )}
          </div>

          {canDownload && (
            <Button
              className="w-full gap-2"
              onClick={() => window.open(`/api/shares/${token}/download`)}
            >
              <Download className="h-4 w-4" />
              Download
            </Button>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
