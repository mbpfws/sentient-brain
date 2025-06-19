import { PrismaClient, Guide, Implementation, Project } from '../generated/prisma';

const prisma = new PrismaClient();

// Type definitions for creating new entries
export type GuideCreateInput = {
    title: string;
    description: string;
    project_alias: string;
};

export type ImplementationCreateInput = {
    title: string;
    code_snippet: string;
    description?: string;
    guide_id: number;
};

/**
 * Creates a new guide and links it to a project.
 */
export async function createGuide(data: GuideCreateInput): Promise<Guide | null> {
    const project = await prisma.project.findUnique({ where: { alias: data.project_alias } });
    if (!project) {
        console.error(`[Guides] Project with alias '${data.project_alias}' not found.`);
        return null;
    }

    const guide = await prisma.guide.create({
        data: {
            title: data.title,
            description: data.description,
            project_id: project.id,
        },
    });
    console.log(`[Guides] Created new guide: '${guide.title}'`);
    return guide;
}

/**
 * Finds guides based on a search query.
 */
export async function findGuides(project_alias: string, query: string): Promise<Guide[]> {
     const guides = await prisma.guide.findMany({
        where: {
            project: {
                alias: project_alias,
            },
            OR: [
                { title: { contains: query, mode: 'insensitive' } },
                { description: { contains: query, mode: 'insensitive' } },
            ],
        },
        include: {
            implementations: true,
        }
    });
    return guides;
}

/**
 * Creates a new implementation for a specific guide.
 */
export async function createImplementation(data: ImplementationCreateInput): Promise<Implementation> {
    const implementation = await prisma.implementation.create({
        data: {
            title: data.title,
            code_snippet: data.code_snippet,
            description: data.description,
            guide_id: data.guide_id,
        },
    });
    console.log(`[Guides] Added new implementation '${implementation.title}' to guide ${data.guide_id}`);
    return implementation;
}
