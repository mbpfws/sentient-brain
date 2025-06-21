import { genAI } from '../lib/gemini-client.js';
// import { getFileContent } from './file-system.service.js'; // This service does not exist yet.

/**
 * Generates a brief, one-sentence description of a code file using the Gemini API.
 * @param filePath The path to the file.
 * @returns A promise that resolves to the AI-generated description.
 */
export async function generateAiDescription(fileContent: string): Promise<string> {
    try {
        if (!fileContent) {
            return 'File content is empty.';
        }

        // Basic check for binary content
        if (fileContent.includes('\uFFFD')) {
            return 'File appears to be binary and will not be described.';
        }

        const prompt = `Provide a concise, one-sentence summary of the purpose of this code file:\n\n---\n${fileContent}\n---\n\nSummary:`;
        
        const result = await genAI.models.generateContent({
            model: 'gemini-2.5-flash', // KEEP this model unchanged
            contents: [{ role: "user", parts: [{ text: prompt }] }],
        });

        const text = result.candidates?.[0]?.content?.parts?.[0]?.text;

        if (!text) {
            console.error("[CodeIndexing] Gemini response is empty or has an unexpected structure:", JSON.stringify(result, null, 2));
            return 'Could not generate AI description.';
        }
        return text;

    } catch (error) {
        console.error(`[Gemini] Error generating description:`, error);
        return 'Could not generate AI description.';
    }
}
