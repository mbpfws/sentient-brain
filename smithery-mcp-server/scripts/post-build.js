const fs = require('fs');
const path = require('path');

// The root of the project where node_modules and .smithery are located
const projectRoot = path.resolve(__dirname, '..');

// Define source path. Crawlee nests jsdom, so we need to go deep.
const sourcePath = path.join(
  projectRoot,
  'node_modules',
  '@crawlee',
  'jsdom',
  'node_modules',
  'jsdom',
  'lib',
  'jsdom',
  'living',
  'xhr',
  'xhr-sync-worker.js'
);

const destinationDir = path.join(projectRoot, '.smithery');
const destinationPath = path.join(destinationDir, 'xhr-sync-worker.js');

console.log('Post-build script running...');

// Check if the source file exists before attempting to copy
if (!fs.existsSync(sourcePath)) {
  console.error(`Error: Source file not found at ${sourcePath}`);
  console.error('This might be due to a change in node_modules structure. Please check the path.');
  // Try an alternative path for flattened dependencies
  const alternativeSourcePath = path.join(projectRoot, 'node_modules', 'jsdom', 'lib', 'jsdom', 'living', 'xhr', 'xhr-sync-worker.js');
  if (fs.existsSync(alternativeSourcePath)) {
    console.log(`Found file at alternative path: ${alternativeSourcePath}`);
    fs.copyFileSync(alternativeSourcePath, destinationPath);
    console.log(`Successfully copied worker file from alternative path to ${destinationPath}`);
    process.exit(0);
  } else {
    console.error('Alternative path also not found. Post-build script failed.');
    process.exit(1);
  }
} else {
  // Ensure the destination directory exists
  if (!fs.existsSync(destinationDir)){
      console.error(`Error: Destination directory ${destinationDir} does not exist. Run 'smithery build' first.`);
      process.exit(1);
  }
  
  // Copy the file
  fs.copyFileSync(sourcePath, destinationPath);
  console.log(`Successfully copied worker file from ${sourcePath} to ${destinationPath}`);
}

console.log('Post-build script finished.');
