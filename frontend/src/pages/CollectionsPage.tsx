import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { FolderOpen, Plus } from "lucide-react";
import { useCollections, useCreateCollection } from "@/api/useCollections";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";

export function CollectionsPage() {
  const navigate = useNavigate();
  const { data, isLoading } = useCollections();
  const createMutation = useCreateCollection();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  const collections = data?.items ?? [];

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    createMutation.mutate(
      { name: name.trim(), description: description.trim() || undefined },
      {
        onSuccess: () => {
          setDialogOpen(false);
          setName("");
          setDescription("");
          toast.success("Collection created");
        },
      }
    );
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-48" />
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-32 rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight">Collections</h1>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger render={
            <Button size="sm">
              <Plus className="mr-1 h-4 w-4" />
              New Collection
            </Button>
          } />
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Collection</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Name</label>
                <Input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Collection name"
                  required
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Description</label>
                <Input
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Optional description"
                />
              </div>
              <DialogFooter>
                <Button type="submit" disabled={createMutation.isPending}>
                  {createMutation.isPending ? "Creating..." : "Create"}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {collections.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
          <FolderOpen className="mb-4 h-10 w-10" />
          <p className="text-lg font-medium">No collections yet</p>
          <p className="text-sm">Create a collection to organize your assets</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
          {collections.map((col) => (
            <Card
              key={col.id}
              className="cursor-pointer transition-shadow hover:shadow-md"
              onClick={() => navigate(`/collections/${col.id}`)}
            >
              <CardContent className="flex flex-col items-center justify-center py-6">
                <FolderOpen className="mb-2 h-8 w-8 text-muted-foreground" />
                <p className="text-sm font-medium truncate w-full text-center">
                  {col.name}
                </p>
                <p className="text-xs text-muted-foreground">
                  {col.asset_count} asset{col.asset_count !== 1 ? "s" : ""}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
