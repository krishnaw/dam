import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { SearchBar } from "../search/SearchBar";

// --- Mocks ---

const mockNavigate = vi.fn();
vi.mock("react-router-dom", () => ({
  useNavigate: () => mockNavigate,
}));

vi.mock("@/components/ui/input", () => ({
  Input: (props: any) => <input {...props} />,
}));

vi.mock("@/components/ui/button", () => ({
  Button: ({ children, ...props }: any) => <button {...props}>{children}</button>,
}));

// --- Tests ---

describe("SearchBar", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders with placeholder text", () => {
    render(<SearchBar />);
    expect(screen.getByPlaceholderText("Search assets...")).toBeInTheDocument();
  });

  it("initializes input with initialQuery value", () => {
    render(<SearchBar initialQuery="landscapes" />);
    const input = screen.getByPlaceholderText("Search assets...");
    expect(input).toHaveValue("landscapes");
  });

  it("calls onSearch callback with trimmed value on submit", () => {
    const onSearch = vi.fn();
    render(<SearchBar onSearch={onSearch} />);

    const input = screen.getByPlaceholderText("Search assets...");
    fireEvent.change(input, { target: { value: "  mountains  " } });

    const submitButton = screen.getByText("Search");
    fireEvent.click(submitButton);

    expect(onSearch).toHaveBeenCalledWith("mountains");
  });

  it("navigates to /search?q=... when no onSearch provided", () => {
    render(<SearchBar />);

    const input = screen.getByPlaceholderText("Search assets...");
    fireEvent.change(input, { target: { value: "sunset" } });

    const submitButton = screen.getByText("Search");
    fireEvent.click(submitButton);

    expect(mockNavigate).toHaveBeenCalledWith("/search?q=sunset");
  });

  it("encodes special characters in the search URL", () => {
    render(<SearchBar />);

    const input = screen.getByPlaceholderText("Search assets...");
    fireEvent.change(input, { target: { value: "a & b" } });

    const submitButton = screen.getByText("Search");
    fireEvent.click(submitButton);

    expect(mockNavigate).toHaveBeenCalledWith("/search?q=a%20%26%20b");
  });

  it("does not navigate when query is empty", () => {
    render(<SearchBar />);

    const submitButton = screen.getByText("Search");
    fireEvent.click(submitButton);

    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it("shows clear button when query has text", () => {
    render(<SearchBar initialQuery="test" />);
    // The X clear button should be present
    const buttons = screen.getAllByRole("button");
    // There should be the clear button + submit button
    expect(buttons.length).toBeGreaterThanOrEqual(2);
  });

  it("does not show clear button when query is empty", () => {
    render(<SearchBar />);
    // Only the submit button should be present
    const buttons = screen.getAllByRole("button");
    expect(buttons).toHaveLength(1);
    expect(buttons[0]).toHaveTextContent("Search");
  });

  it("clear button resets query and calls onSearch with empty string", () => {
    const onSearch = vi.fn();
    render(<SearchBar initialQuery="test query" onSearch={onSearch} />);

    // Find the clear button (the one that is NOT the submit button)
    const buttons = screen.getAllByRole("button");
    const clearButton = buttons.find((b) => b.textContent !== "Search")!;
    fireEvent.click(clearButton);

    const input = screen.getByPlaceholderText("Search assets...");
    expect(input).toHaveValue("");
    expect(onSearch).toHaveBeenCalledWith("");
  });
});
