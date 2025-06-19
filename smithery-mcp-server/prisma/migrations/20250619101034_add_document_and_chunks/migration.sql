-- CreateTable
CREATE TABLE "Document" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "source_url" TEXT,
    "file_path" TEXT,
    "title" TEXT,
    "markdown_content" TEXT NOT NULL,
    "content_hash" TEXT NOT NULL,
    "created_at" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" DATETIME NOT NULL,
    "project_id" INTEGER NOT NULL,
    CONSTRAINT "Document_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "Project" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "DocumentChunk" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "document_id" INTEGER NOT NULL,
    "chunk_text" TEXT NOT NULL,
    "order" INTEGER NOT NULL,
    "created_at" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" DATETIME NOT NULL,
    CONSTRAINT "DocumentChunk_document_id_fkey" FOREIGN KEY ("document_id") REFERENCES "Document" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);

-- CreateIndex
CREATE UNIQUE INDEX "Document_content_hash_key" ON "Document"("content_hash");

-- CreateIndex
CREATE INDEX "Document_project_id_idx" ON "Document"("project_id");

-- CreateIndex
CREATE INDEX "Document_content_hash_idx" ON "Document"("content_hash");

-- CreateIndex
CREATE INDEX "DocumentChunk_document_id_idx" ON "DocumentChunk"("document_id");
