/**
 * QuickSort Algorithm Implementation in JavaScript
 * 
 * Multiple variants provided:
 * 1. Classic in-place quicksort
 * 2. Functional approach with new arrays
 * 3. Randomized pivot selection
 * 4. Three-way partitioning (Dutch National Flag)
 */

// ============================================
// 1. Classic In-Place QuickSort
// ============================================
function quickSort(arr, low = 0, high = arr.length - 1) {
    if (low < high) {
        // Partition the array and get pivot index
        const pivotIndex = partition(arr, low, high);
        
        // Recursively sort elements before and after partition
        quickSort(arr, low, pivotIndex - 1);
        quickSort(arr, pivotIndex + 1, high);
    }
    return arr;
}

function partition(arr, low, high) {
    // Choose the rightmost element as pivot
    const pivot = arr[high];
    let i = low - 1; // Index of smaller element
    
    for (let j = low; j < high; j++) {
        // If current element is smaller than or equal to pivot
        if (arr[j] <= pivot) {
            i++;
            [arr[i], arr[j]] = [arr[j], arr[i]]; // Swap elements
        }
    }
    
    // Place pivot in correct position
    [arr[i + 1], arr[high]] = [arr[high], arr[i + 1]];
    return i + 1;
}

// ============================================
// 2. Functional QuickSort (Creates New Arrays)
// ============================================
function quickSortFunctional(arr) {
    if (arr.length <= 1) {
        return arr;
    }
    
    const pivot = arr[Math.floor(arr.length / 2)];
    const left = arr.filter(x => x < pivot);
    const middle = arr.filter(x => x === pivot);
    const right = arr.filter(x => x > pivot);
    
    return [
        ...quickSortFunctional(left),
        ...middle,
        ...quickSortFunctional(right)
    ];
}

// ============================================
// 3. Randomized QuickSort (Better Average Performance)
// ============================================
function quickSortRandomized(arr, low = 0, high = arr.length - 1) {
    if (low < high) {
        // Randomly select pivot to avoid worst-case O(n²)
        const randomPivot = low + Math.floor(Math.random() * (high - low + 1));
        [arr[randomPivot], arr[high]] = [arr[high], arr[randomPivot]];
        
        const pivotIndex = partition(arr, low, high);
        quickSortRandomized(arr, low, pivotIndex - 1);
        quickSortRandomized(arr, pivotIndex + 1, high);
    }
    return arr;
}

// ============================================
// 4. Three-Way QuickSort (Handles Duplicates Efficiently)
// ============================================
function quickSort3Way(arr, low = 0, high = arr.length - 1) {
    if (low < high) {
        const [lt, gt] = partition3Way(arr, low, high);
        quickSort3Way(arr, low, lt - 1);
        quickSort3Way(arr, gt + 1, high);
    }
    return arr;
}

function partition3Way(arr, low, high) {
    const pivot = arr[low];
    let lt = low;      // arr[low..lt-1] < pivot
    let i = low + 1;   // arr[lt..i-1] == pivot
    let gt = high;     // arr[gt+1..high] > pivot
    
    while (i <= gt) {
        if (arr[i] < pivot) {
            [arr[lt], arr[i]] = [arr[i], arr[lt]];
            lt++;
            i++;
        } else if (arr[i] > pivot) {
            [arr[i], arr[gt]] = [arr[gt], arr[i]];
            gt--;
        } else {
            i++;
        }
    }
    
    return [lt, gt];
}

// ============================================
// 5. Utility Functions & Performance Testing
// ============================================
function generateRandomArray(size, max = 1000) {
    return Array.from({ length: size }, () => Math.floor(Math.random() * max));
}

function measurePerformance(sortFunction, arr, label) {
    const testArr = [...arr]; // Create copy to avoid mutation
    const start = performance.now();
    sortFunction(testArr);
    const end = performance.now();
    console.log(`${label}: ${(end - start).toFixed(2)}ms`);
    return testArr;
}

// ============================================
// 6. Example Usage & Testing
// ============================================
function demonstrateQuickSort() {
    console.log("=== QuickSort Algorithm Demonstration ===\n");
    
    // Test with small array
    const smallArray = [64, 34, 25, 12, 22, 11, 90, 5];
    console.log("Original array:", smallArray);
    console.log("Sorted (classic):", quickSort([...smallArray]));
    console.log("Sorted (functional):", quickSortFunctional([...smallArray]));
    console.log("Sorted (randomized):", quickSortRandomized([...smallArray]));
    console.log("Sorted (3-way):", quickSort3Way([...smallArray]));
    
    // Performance comparison
    console.log("\n=== Performance Comparison (1000 elements) ===");
    const largeArray = generateRandomArray(1000);
    
    measurePerformance(arr => quickSort([...arr]), largeArray, "Classic QuickSort");
    measurePerformance(quickSortFunctional, largeArray, "Functional QuickSort");
    measurePerformance(arr => quickSortRandomized([...arr]), largeArray, "Randomized QuickSort");
    measurePerformance(arr => quickSort3Way([...arr]), largeArray, "3-Way QuickSort");
}

// ============================================
// 7. Export for Module Usage
// ============================================
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        quickSort,
        quickSortFunctional,
        quickSortRandomized,
        quickSort3Way,
        generateRandomArray,
        measurePerformance,
        demonstrateQuickSort
    };
}

// Run demonstration if script is executed directly
if (typeof window === 'undefined' && require.main === module) {
    demonstrateQuickSort();
} 