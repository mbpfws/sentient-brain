-- CreateTable
CREATE TABLE "Project" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "alias" TEXT NOT NULL,
    "root_path" TEXT NOT NULL,
    "description" TEXT,
    "created_at" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" DATETIME NOT NULL
);

-- CreateTable
CREATE TABLE "CodeFile" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "file_path" TEXT NOT NULL,
    "file_name" TEXT NOT NULL,
    "parent_directory" TEXT NOT NULL,
    "file_hash" TEXT NOT NULL,
    "size_bytes" INTEGER NOT NULL,
    "last_modified_at_fs" DATETIME NOT NULL,
    "description" TEXT,
    "created_at" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" DATETIME NOT NULL,
    "project_id" INTEGER NOT NULL,
    CONSTRAINT "CodeFile_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "Project" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);

-- CreateIndex
CREATE UNIQUE INDEX "Project_alias_key" ON "Project"("alias");

-- CreateIndex
CREATE UNIQUE INDEX "CodeFile_file_path_key" ON "CodeFile"("file_path");

-- CreateIndex
CREATE INDEX "CodeFile_project_id_idx" ON "CodeFile"("project_id");
