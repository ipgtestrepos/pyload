# Intellectual Property (IP) Composition
The following flowchart illustrates the structure of an Intellectual Property (IP) that is composed of several files. Each file serves a specific purpose and contributes to the overall functionality of the IP.

```mermaid
graph TD;
    IP["Intellectual Property (IP)"]
    sourceFiles["Source Files"]
    headerFiles["Header Files"]
    configFiles["Configuration Files"]
    docFiles["Documentation Files"]
    testFiles["Test Files"]

    IP --> sourceFiles
    IP --> headerFiles
    IP --> configFiles
    IP --> docFiles
    IP --> testFiles

    sourceFiles --> file1["file1.c"]
    sourceFiles --> file2["file2.cpp"]

    headerFiles --> file3["file1.h"]
    headerFiles --> file4["file2.hpp"]

    configFiles --> file5["config.xml"]
    configFiles --> file6["settings.json"]

    docFiles --> file7["README.md"]
    docFiles --> file8["user_guide.pdf"]

    testFiles --> file9["test1.cpp"]
    testFiles --> file10["test2.py"]
```

## Image 1 - diagram
![chip3.png](./doc/chip3.png)

## Documentation file
[doc.pdf](./doc/doc.pdf)

## Example of module
The following is an example of a module that can be used in the IP. This module is written in Verilog. 

```Verilog
module top;
    reg clk;
    reg [7:0] data;
    wire [7:0] result;

    // Instantiate the unit under test (UUT)
    sample uut (
        .clk(clk),
        .data(data),
        .result(result)
    );

    initial begin
        // Initialize Inputs
        clk = 0;
        data = 8'hFF;

        // Wait 100 ns for global reset to finish
        #100;

        // Add stimulus here
    end

    always begin
        #5 clk = ~clk;
    end

endmodule
```

## Image 2 - diagram
![chip2.jpg](./doc/chip2.jpg)
