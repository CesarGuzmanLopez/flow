import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';

@Component({
  selector: 'app-editor',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="editor">
      <div class="editor-toolbar">
        <h2>Flow Editor</h2>
        <div class="toolbar-actions">
          <button>Save</button>
          <button>Execute</button>
        </div>
      </div>
      <div class="editor-content">
        <div class="canvas">
          <p class="placeholder">Canvas for flow visualization will be here</p>
          <p class="note">This will use a drag-and-drop library for step-first flow design</p>
        </div>
        <div class="properties-panel">
          <h3>Properties</h3>
          <p>Select a step to view its properties</p>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .editor {
      display: flex;
      flex-direction: column;
      height: 100vh;
    }

    .editor-toolbar {
      background: white;
      padding: 1rem 2rem;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    h2 {
      margin: 0;
      color: #333;
    }

    .toolbar-actions {
      display: flex;
      gap: 1rem;
    }

    button {
      padding: 0.5rem 1rem;
      background: #667eea;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
    }

    button:hover {
      background: #5568d3;
    }

    .editor-content {
      display: flex;
      flex: 1;
      overflow: hidden;
    }

    .canvas {
      flex: 1;
      background: #f5f7fa;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      padding: 2rem;
    }

    .placeholder {
      font-size: 1.25rem;
      color: #666;
      margin-bottom: 0.5rem;
    }

    .note {
      color: #999;
      font-size: 0.875rem;
    }

    .properties-panel {
      width: 300px;
      background: white;
      border-left: 1px solid #e2e8f0;
      padding: 1.5rem;
      overflow-y: auto;
    }

    h3 {
      margin-top: 0;
      color: #333;
    }
  `]
})
export class EditorComponent {}
