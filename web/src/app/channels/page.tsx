"use client";

import { useState, useEffect, useCallback } from "react";
import { Radio, Loader2, CheckCircle2, XCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { listChannels, type Channel } from "@/lib/api";

const channelIcons: Record<string, string> = {
  Telegram: "📱",
  "Microsoft Teams": "💬",
  "Web UI": "🌐",
};

export default function ChannelsPage() {
  const [channels, setChannels] = useState<Channel[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchChannels = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listChannels();
      setChannels(data.channels);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch channels");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchChannels();
  }, [fetchChannels]);

  return (
    <div className="flex h-full flex-col">
      <div className="border-b px-4 py-3 sm:px-6">
        <h1 className="text-lg font-semibold flex items-center gap-2">
          <Radio className="h-5 w-5" /> Channels
        </h1>
        <p className="text-xs text-muted-foreground">
          Connected messaging channels and their status
        </p>
      </div>

      <div className="p-4 sm:p-6">
        {error && (
          <div className="mb-4 rounded-lg border border-destructive bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {channels.map((channel) => (
              <Card key={channel.name}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <span className="text-xl">{channelIcons[channel.name] ?? "📡"}</span>
                      {channel.name}
                    </CardTitle>
                    <Badge variant={channel.configured ? "default" : "secondary"}>
                      {channel.configured ? "Configured" : "Not Set Up"}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-2 text-sm">
                    {channel.status === "active" ? (
                      <>
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                        <span className="text-green-500">Active</span>
                      </>
                    ) : (
                      <>
                        <XCircle className="h-4 w-4 text-muted-foreground" />
                        <span className="text-muted-foreground">Not configured</span>
                      </>
                    )}
                  </div>
                  <CardDescription className="mt-3 text-xs">
                    {channel.name === "Telegram" &&
                      "Set EREBUS_TELEGRAM_TOKEN to enable the Telegram bot."}
                    {channel.name === "Microsoft Teams" &&
                      "Set EREBUS_TEAMS_APP_ID and EREBUS_TEAMS_APP_PASSWORD to enable Teams."}
                    {channel.name === "Web UI" &&
                      "The web interface is always available."}
                  </CardDescription>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
