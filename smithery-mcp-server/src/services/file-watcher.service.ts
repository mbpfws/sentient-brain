import * as chokidar from 'chokidar';
import * as path from 'path';
import { PrismaClient, Project } from '../generated/prisma/index.js';
import { updateOrCreateCodeFileByPath, deleteCodeFileByPath } from './code-indexing.service.js';

const prisma = new PrismaClient();

class WatcherService {
    private watchers: Map<string, chokidar.FSWatcher> = new Map();

    public async start(): Promise<void> {
        console.log('[Watcher] Starting service...');
        const projects = await prisma.project.findMany();
        for (const project of projects) {
            this.watchProject(project);
        }
    }

    public watchProject(project: Project): void {
        if (this.watchers.has(project.alias)) {
            console.log(`[Watcher] Project '${project.alias}' is already being watched.`);
            return;
        }

        const projectPath = path.resolve(project.root_path);
        console.log(`[Watcher] Initializing watcher for project '${project.alias}' at ${projectPath}`);

        const watcher = chokidar.watch(projectPath, {
            ignored: [
                /(^|[\\/\\])\../, // ignore dotfiles
                /node_modules/,
                /\.git/,
                /__pycache__/,
                /\.vscode/,
                /\.idea/,
                /prisma/, // Ignore the prisma directory
            ],
            persistent: true,
            ignoreInitial: true,
            awaitWriteFinish: {
                stabilityThreshold: 2000,
                pollInterval: 100,
            },
        });

        watcher
            .on('add', (filePath) => {
                console.log(`[Watcher] File added: ${filePath}`);
                updateOrCreateCodeFileByPath(project.alias, path.resolve(filePath));
            })
            .on('change', (filePath) => {
                console.log(`[Watcher] File changed: ${filePath}`);
                updateOrCreateCodeFileByPath(project.alias, path.resolve(filePath));
            })
            .on('unlink', (filePath) => {
                console.log(`[Watcher] File deleted: ${filePath}`);
                deleteCodeFileByPath(path.resolve(filePath));
            })
            .on('error', (error) => console.error(`[Watcher] Error: ${error}`))
            .on('ready', () => console.log(`[Watcher] Initial scan complete for '${project.alias}'. Ready for changes.`));

        this.watchers.set(project.alias, watcher);
    }

    public stop(): void {
        console.log('[Watcher] Stopping all watchers...');
        this.watchers.forEach((watcher, alias) => {
            watcher.close();
            console.log(`[Watcher] Stopped watching project '${alias}'.`);
        });
        this.watchers.clear();
    }
}

// Create and export a singleton instance of the service
export const fileWatcherService = new WatcherService();
