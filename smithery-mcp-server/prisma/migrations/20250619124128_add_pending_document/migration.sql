-- CreateTable
CREATE TABLE "PendingDocument" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "project_id" INTEGER NOT NULL,
    "url" TEXT NOT NULL,
    "title" TEXT,
    "status" TEXT NOT NULL DEFAULT 'DISCOVERED',
    "discovery_method" TEXT,
    "depth" INTEGER,
    "last_attempted_at" DATETIME,
    "error_message" TEXT,
    "created_at" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" DATETIME NOT NULL,
    CONSTRAINT "PendingDocument_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "Project" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);

-- CreateIndex
CREATE INDEX "PendingDocument_project_id_idx" ON "PendingDocument"("project_id");

-- CreateIndex
CREATE INDEX "PendingDocument_status_idx" ON "PendingDocument"("status");

-- CreateIndex
CREATE UNIQUE INDEX "PendingDocument_project_id_url_key" ON "PendingDocument"("project_id", "url");
