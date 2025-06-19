import { PrismaClient, Project, CodeFile } from '../generated/prisma';

// Utility to add a delay
const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));
import { promises as fs } from 'fs';
import * as path from 'path';
import * as crypto from 'crypto';
import { genAI } from '../lib/gemini-client.js';

// Initialize Prisma client
const prisma = new PrismaClient();

/**
 * Computes and returns the SHA-256 hash of the file at the specified path.
 *
 * @param filePath - Path to the file whose hash will be calculated
 * @returns A promise that resolves to the hexadecimal SHA-256 hash string of the file's contents
 */
async function getFileHash(filePath: string): Promise<string> {
    const fileBuffer = await fs.readFile(filePath);
    const hashSum = crypto.createHash('sha256');
    hashSum.update(fileBuffer);
    return hashSum.digest('hex');
}

/**
 * Generates a concise, one-sentence summary of a code file's purpose using the Gemini AI model.
 *
 * Returns a fallback message if the file is too large, appears binary, or if AI generation fails.
 *
 * @param filePath - Path to the code file to summarize
 * @returns The AI-generated description or a fallback message
 */
async function generateAiDescription(filePath: string): Promise<string> {
    try {
        const fileContent = await fs.readFile(filePath, 'utf-8');
        // Limit file size to avoid excessive API usage
        if (fileContent.length > 1000000) {
            return 'File is too large to generate a description.';
        }

        // Basic check for binary files by looking for null characters
        if (fileContent.includes('\u0000')) {
            return 'File appears to be binary and will not be described.';
        }

        const model = genAI.getGenerativeModel({ model: 'gemini-1.5-flash' });
        const prompt = `Provide a concise, one-sentence summary of the purpose of this code file:

---
${fileContent}
---

Summary:`;

        const result = await model.generateContent(prompt);
        const response = await result.response;
        return response.text().trim();
    } catch (error) {
        console.error(`[Gemini] Error generating description for ${filePath}:`, error);
        return 'Could not generate AI description.';
    }
}

/**
 * Recursively indexes all files in a project's codebase directory, storing file metadata and AI-generated descriptions in the database.
 *
 * @param projectAlias - The unique alias identifying the project.
 * @param rootPath - The root directory path of the codebase to index.
 * @returns The created project if a new project record was made; otherwise, null.
 */
export async function indexCodebase(projectAlias: string, rootPath: string): Promise<Project | null> {
    console.log(`[Indexer] Starting indexing for project '${projectAlias}' at ${rootPath}`);

    // Find or create the project
    let project = await prisma.project.findUnique({
        where: { alias: projectAlias },
    });

    let isNewProject = false;
    if (!project) {
        project = await prisma.project.create({
            data: { alias: projectAlias, root_path: rootPath },
        });
        isNewProject = true;
        console.log(`[Indexer] Created new project: ${project.alias}`);
    }

    const absoluteRootPath = path.resolve(rootPath);
    const ignoredDirectories = ['node_modules', '.git', '__pycache__', '.vscode', '.idea', 'prisma'];

    /**
     * Recursively scans a directory, indexing each file by storing its metadata and an AI-generated description in the database.
     *
     * Skips ignored and hidden directories. For each file, computes its hash, gathers metadata, generates a summary, and upserts the information into the database. Introduces a delay between file operations to respect external API rate limits.
     *
     * @param directory - The absolute path of the directory to scan recursively
     */
    async function scanDirectory(directory: string) {
        const entries = await fs.readdir(directory, { withFileTypes: true });

        for (const entry of entries) {
            const fullPath = path.join(directory, entry.name);
            if (entry.isDirectory()) {
                if (!ignoredDirectories.includes(entry.name) && !entry.name.startsWith('.')) {
                    await scanDirectory(fullPath);
                }
            } else if (entry.isFile()) {
                try {
                    // Add a delay to respect API rate limits
                    await sleep(4000); // 4 seconds delay -> 15 requests per minute

                    const stats = await fs.stat(fullPath);
                    const fileHash = await getFileHash(fullPath);
                    const aiDescription = await generateAiDescription(fullPath);

                    await prisma.codeFile.upsert({
                        where: { file_path: fullPath },
                        update: {
                            file_hash: fileHash,
                            size_bytes: stats.size,
                            last_modified_at_fs: stats.mtime,
                            description: aiDescription,
                            updated_at: new Date(),
                        },
                        create: {
                            file_path: fullPath,
                            file_name: entry.name,
                            parent_directory: path.dirname(fullPath),
                            project_id: project!.id,
                            file_hash: fileHash,
                            size_bytes: stats.size,
                            last_modified_at_fs: stats.mtime,
                            description: aiDescription,
                        },
                    });
                    console.log(`[Indexer] Upserted: ${fullPath}`);
                } catch (error) {
                    console.error(`[Indexer] Failed to process file ${fullPath}:`, error);
                }
            }
        }
    }

    await scanDirectory(absoluteRootPath);

    console.log(`[Indexer] Finished indexing for project '${projectAlias}'.`);
    return isNewProject ? project : null;
}

/**
 * Updates or creates a code file entry in the database for the specified file path within a project.
 *
 * If the project does not exist, the operation is skipped. Intended for use by file watchers to synchronize file metadata and AI-generated descriptions with the database. Handles cases where the file may have been deleted before processing.
 *
 * @param projectAlias - The alias of the project.
 * @param filePath - The absolute path to the file.
 */
export async function updateOrCreateCodeFileByPath(projectAlias: string, filePath: string): Promise<void> {
    const project = await prisma.project.findUnique({ where: { alias: projectAlias } });
    if (!project) {
        console.error(`[Watcher] Project '${projectAlias}' not found for file update: ${filePath}`);
        return;
    }

    try {
        // Add a delay to respect API rate limits
        await sleep(4000); // 4 seconds delay -> 15 requests per minute

        const stats = await fs.stat(filePath);
        if (!stats.isFile()) return;

        const fileHash = await getFileHash(filePath);
        const aiDescription = await generateAiDescription(filePath);

        await prisma.codeFile.upsert({
            where: { file_path: filePath },
            update: {
                file_hash: fileHash,
                size_bytes: stats.size,
                last_modified_at_fs: stats.mtime,
                description: aiDescription,
                updated_at: new Date(),
            },
            create: {
                file_path: filePath,
                file_name: path.basename(filePath),
                parent_directory: path.dirname(filePath),
                project_id: project.id,
                file_hash: fileHash,
                size_bytes: stats.size,
                last_modified_at_fs: stats.mtime,
                description: aiDescription,
            },
        });
        console.log(`[Watcher] Upserted file: ${filePath}`);
    } catch (error: any) {
        // If file doesn't exist (e.g., deleted just after event fired), ignore error.
        if (error.code !== 'ENOENT') {
            console.error(`[Watcher] Failed to process file ${filePath}:`, error);
        }
    }
}

/**
 * Removes a code file record from the database by its absolute file path.
 *
 * If the file record does not exist, the operation is silently ignored.
 */
export async function deleteCodeFileByPath(filePath: string): Promise<void> {
    try {
        await prisma.codeFile.delete({
            where: { file_path: filePath },
        });
        console.log(`[Watcher] Deleted file from index: ${filePath}`);
    } catch (error: any) {
        // Ignore if file was already deleted from DB (Prisma's P2025 error)
        if (error.code !== 'P2025') {
            console.error(`[Watcher] Failed to delete file ${filePath}:`, error);
        }
    }
}
