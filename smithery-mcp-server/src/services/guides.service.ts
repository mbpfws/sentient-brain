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
 * Creates a new guide associated with a project identified by its alias.
 *
 * If the specified project does not exist, returns null.
 *
 * @param data - Input containing the guide's title, description, and the target project's alias
 * @returns The created guide, or null if the project is not found
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
 * Retrieves guides for a specified project whose title or description matches the search query.
 *
 * @param project_alias - The alias identifying the project whose guides are being searched
 * @param query - The search string to match against guide titles and descriptions
 * @returns An array of guides matching the query, each including their related implementations
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
 * Creates a new implementation entry linked to a specified guide.
 *
 * @param data - The implementation details, including title, code snippet, optional description, and the guide ID to associate with.
 * @returns The newly created implementation.
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
