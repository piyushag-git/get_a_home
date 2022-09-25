import React from 'react';
//import renderer from 'react-test-renderer';
import App from './App';

/*

test('renders correctly', () => {
    const tree = renderer.create(<App />).toJSON();
    expect(tree).toMatchSnapshot();
  });
  */
  


test('given empty GroceryShoppingList, user can add an item to it', () => {
const { getByPlaceholder, getByText, getAllByText } = render(
    <PostCodeButton />
);

fireEvent.changeText(
    getByPlaceholder('Enter grocery item'),
    'banana'
);
fireEvent.press(getByText('Add the item to list'));

const bananaElements = getAllByText('banana');
expect(bananaElements).toHaveLength(1);
}); 